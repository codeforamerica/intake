import importlib
from django.conf import settings
from django.db import models
from pytz import timezone
import uuid
from django.utils import timezone as timezone_utils
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

from intake import pdfparser, anonymous_names, notifications
from intake.constants import CONTACT_METHOD_CHOICES



def gen_uuid():
    return uuid.uuid4().hex

def get_parser():
    parser = pdfparser.PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
        'intake/pdfparser.jar')
    return parser


class FormSubmission(models.Model):

    answers = JSONField()
    # old_uuid is only used for porting legacy applications
    old_uuid = models.CharField(max_length=34, unique=True,
        default=gen_uuid)
    anonymous_name = models.CharField(max_length=60,
        default=anonymous_names.generate)
    date_received = models.DateTimeField(default=timezone_utils.now)

    class Meta:
        ordering = ['-date_received']

    @classmethod
    def create_from_answers(cls, post_data):
        cleaned = {}
        for key, value in post_data.items():
            cleaned[key] = value[0]
        instance = cls(answers=cleaned)
        instance.save()
        return instance

    @classmethod
    def mark_viewed(cls, submissions, user):
        logs = ApplicationLogEntry.log_opened(
            [s.id for s in submissions], user)
        # send a slack notification
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=user)
        return submissions, logs

    @classmethod
    def refer_unopened_apps(cls):
        users = User.objects.filter(profile__should_get_notifications=True)
        emails = [user.email for user in users]
        submissions = cls.get_unopened_apps()
        submission_ids=[s.id for s in submissions]
        if submissions:
            count = len(submission_ids)
            notifications.front_email_daily_app_bundle.send(
                to=emails,
                count=count,
                submission_ids=submission_ids
                )
            ApplicationLogEntry.log_referred(submission_ids, user=None)
        notifications.slack_app_bundle_sent.send(submissions=submissions, emails=emails)
        return notifications.slack_app_bundle_sent.render(submissions=submissions, emails=emails)

    @classmethod
    def get_unopened_apps(cls):
        return cls.objects.exclude(
            logs__user__profile__organization__is_receiving_agency=True
            )

    @classmethod
    def get_opened_apps(cls):
        return cls.objects.filter(
            logs__user__profile__organization__is_receiving_agency=True
            ).distinct()

    @classmethod
    def all_plus_related_objects(cls):
        return cls.objects.prefetch_related('logs__user__profile__organization').all()

    def agency_event_logs(self, event_type):
        '''assumes that self.logs and self.logs.user are prefetched'''
        for log in self.logs.all():
            if log.user:
                if log.user.profile.organization.is_receiving_agency:
                    if log.event_type == event_type:
                        yield log

    def agency_log_time(self, event_type, reduce_func=max):
        return reduce_func((log.time for log in self.agency_event_logs(
            event_type)), default=None)

    def first_opened_by_agency(self):
        return self.agency_log_time(ApplicationLogEntry.OPENED, min)

    def last_opened_by_agency(self):
        return self.agency_log_time(ApplicationLogEntry.OPENED, max)

    def last_processed_by_agency(self):
        return self.agency_log_time(ApplicationLogEntry.PROCESSED, max)

    def get_local_date_received(self, fmt, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        return self.date_received.astimezone(local_tz).strftime(fmt)

    def get_contact_preferences(self):
        preferences = []
        for k in self.answers:
            if "prefers" in k:
                preferences.append(k[8:])
        return [
            nice for key, nice
            in CONTACT_METHOD_CHOICES
            if key in preferences]

    def get_anonymous_display(self):
        return self.anonymous_name

    def __str__(self):
        return self.get_anonymous_display()



class ApplicationLogEntry(models.Model):
    OPENED = 1
    REFERRED = 2
    PROCESSED = 3
    DELETED = 4

    EVENT_TYPES = (
        (OPENED,    "opened"),
        (REFERRED,  "referred"),
        (PROCESSED, "processed"),
        (DELETED,   "deleted"),
        )

    time = models.DateTimeField(default=timezone_utils.now)
    user = models.ForeignKey(User,
        on_delete=models.SET_NULL, null=True,
        related_name='application_logs')
    submission = models.ForeignKey(FormSubmission,
        on_delete=models.SET_NULL, null=True,
        related_name='logs')
    event_type = models.PositiveSmallIntegerField(
        choices=EVENT_TYPES)

    class Meta:
        ordering = ['-time']


    @classmethod
    def log_multiple(cls, event_type, submission_ids, user, time=None):
        if not time:
            time = timezone_utils.now()
        logs = []
        for submission_id in submission_ids:
            log = cls(
                time=time,
                user=user,
                submission_id=submission_id,
                event_type=event_type
                )
            logs.append(log)
        ApplicationLogEntry.objects.bulk_create(logs)
        return logs

    @classmethod
    def log_opened(cls, submission_ids, user, time=None):
        return cls.log_multiple(cls.OPENED, submission_ids, user, time)

    @classmethod
    def log_referred(cls, submission_ids, user, time=None):
        return cls.log_multiple(cls.REFERRED, submission_ids, user, time)

    @classmethod
    def log_processed(cls, submission_ids, user, time=None):
        return cls.log_multiple(cls.PROCESSED, submission_ids, user, time)



class FillablePDF(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='pdfs/')
    translator = models.TextField()

    @classmethod
    def get_default_instance(cls):
        return cls.objects.first()

    def get_pdf(self):
        self.pdf.seek(0)
        return self.pdf

    def get_translator(self):
        import_path_parts = self.translator.split('.')
        callable_name = import_path_parts.pop()
        module_path = '.'.join(import_path_parts)
        module = importlib.import_module(module_path)
        return getattr(module, callable_name)

    def get_pdf_fields(self):
        parser = get_parser()
        data = parser.get_field_data(self.get_pdf())
        return data['fields']

    def __str__(self):
        return self.name

    def fill(self, *args, **kwargs):
        parser = get_parser()
        translator = self.get_translator()
        return parser.fill_pdf(self.get_pdf(), translator(*args, **kwargs))

    def fill_many(self, data_set, *args, **kwargs):
        if data_set:
            parser = get_parser()
            translator = self.get_translator()
            translated = [translator(d, *args, **kwargs)
                            for d in data_set]
            if len(translated) == 1:
                return parser.fill_pdf(self.get_pdf(), translated[0])
            return parser.fill_many_pdfs(self.get_pdf(), translated)
