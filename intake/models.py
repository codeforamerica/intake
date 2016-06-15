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


nice_contact_choices = {
    'voicemail': 'voicemail',
    'sms': 'text message',
    'email': 'email',
    'snailmail': 'paper mail'
}

def gen_uuid():
    return uuid.uuid4().hex

def get_parser():
    parser = pdfparser.PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
        'intake/pdfparser.jar')
    return parser


class FormSubmission(models.Model):

    STEP_FIELDS = [
        'reviewed_by_staff', 'confirmation_sent',
        'submitted_to_agency', 'opened_by_agency',
        'processed_by_agency', 'due_for_followup',
        'followup_sent', 'followup_answered',
        'told_eligible', 'told_ineligible'
    ]

    answers = JSONField()
    # old_uuid is only used for porting legacy applications
    old_uuid = models.CharField(max_length=34, unique=True,
        default=gen_uuid)
    anonymous_name = models.CharField(max_length=60,
        default=anonymous_names.generate)
    date_received = models.DateTimeField(auto_now_add=True)
    reviewed_by_staff = models.DateTimeField(null=True)
    confirmation_sent = models.DateTimeField(null=True)
    submitted_to_agency = models.DateTimeField(null=True)
    opened_by_agency = models.DateTimeField(null=True)
    processed_by_agency = models.DateTimeField(null=True)
    due_for_followup = models.DateTimeField(null=True)
    followup_sent = models.DateTimeField(null=True)
    followup_answered = models.DateTimeField(null=True)
    told_eligible = models.DateTimeField(null=True)
    told_ineligible = models.DateTimeField(null=True)

    @classmethod
    def create_from_answers(cls, post_data):
        cleaned = {}
        for key, value in post_data.items():
            cleaned[key] = value[0]
        instance = cls(answers=cleaned)
        instance.save()
        return instance


    @classmethod
    def mark_step(cls, ids, step, user=None, time=None):
        if step not in cls.STEP_FIELDS:
            raise KeyError(
                "'{}' is not an attribute of {}".format(
                    step, cls.__name__))
        if not time:
            time = timezone_utils.now()
        submissions = cls.objects.filter(pk__in=ids)
        submissions.update(**{step:time})
        logs = ApplicationLogEntry.log_updated(
            submissions, user, time, step
            )
        return submissions, logs

    @classmethod
    def mark_opened_by_agency(cls, submissions, user):
        return cls.mark_step(
            [s.id for s in submissions],
            'opened_by_agency',
            user=user,
            )

    @classmethod
    def mark_viewed(cls, submissions, user):
        if user.email in settings.DEFAULT_AGENCY_USER_EMAILS:
            submissions, logs = cls.mark_opened_by_agency(submissions, user)
        else:
            logs = ApplicationLogEntry.log_read(submissions, user)
        # send a slack notification
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=user)
        return submissions, logs

    @classmethod
    def get_unopened_apps(cls):
        return cls.objects.filter(
            opened_by_agency__isnull=True
            )

    def get_local_date_received(self, fmt, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        return self.date_received.astimezone(local_tz).strftime(fmt)

    def get_contact_preferences(self):
        preferences = []
        for k in self.answers:
            if "prefers" in k:
                preferences.append(k[8:])
        return [nice_contact_choices[m] for m in preferences]

    def get_anonymous_display(self):
        return self.anonymous_name

    def __str__(self):
        return self.get_anonymous_display()



class ApplicationLogEntry(models.Model):
    '''
    '''
    CREATED = 1
    READ = 2
    UPDATED = 3
    DELETED = 4

    ACTION_TYPES = (
        (CREATED, "created"),
        (READ,    "read"   ),
        (UPDATED, "updated"),
        (DELETED, "deleted"), 
        )

    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,
        on_delete=models.SET_NULL, null=True,
        related_name='application_logs')
    submission = models.ForeignKey(FormSubmission,
        on_delete=models.SET_NULL, null=True,
        related_name='logs')
    action_type = models.PositiveSmallIntegerField(
        choices=ACTION_TYPES)
    updated_field = models.CharField(max_length=50,
        blank=True)

    class Meta:
        ordering = ['-time']

    @classmethod
    def log_multiple(cls, action_type, submissions, user, time=None, field=''):
        if not time:
            time = timezone_utils.now()
        logs = []
        for submission in submissions:
            log = cls(
                time=time,
                user=user,
                submission=submission,
                action_type=action_type,
                updated_field=field
                )
            logs.append(log)
        ApplicationLogEntry.objects.bulk_create(logs)
        return logs

    @classmethod
    def log_read(cls, submissions, user, time=None):
        return cls.log_multiple(cls.READ, submissions, user, time)

    @classmethod
    def log_updated(cls, submissions, user, time=None, field=''):
        return cls.log_multiple(cls.UPDATED, submissions, user, time, field)



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
        parser = get_parser()
        translator = self.get_translator()
        return parser.fill_many_pdfs(self.get_pdf(), [
            translator(d, *args, **kwargs)
            for d in data_set
            ])
