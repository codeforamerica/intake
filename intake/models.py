import importlib
import logging
import uuid
import datetime
from urllib.parse import urljoin
import random
from django.conf import settings
from django.db import models
from pytz import timezone
from django.utils import timezone as timezone_utils
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse

from project.jinja2 import namify

from formation import field_types

from intake import (
    pdfparser, anonymous_names, notifications, model_fields,
    constants
)

from formation.forms import display_form_selector

logger = logging.getLogger(__name__)


class MissingAnswersError(Exception):
    pass


class MissingPDFsError(Exception):
    pass


def gen_uuid():
    return uuid.uuid4().hex


def get_parser():
    parser = pdfparser.PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
                                    'intake/pdfparser.jar')
    return parser


class CountyManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class County(models.Model):
    objects = CountyManager()

    slug = models.SlugField()
    name = models.TextField()
    description = models.TextField()


    def get_receiving_agency(self, answers):
        """Returns the appropriate receiving agency
        for this county. Currently there is only one per county,
        but in the future this can be used to make eligibility
        determinations
        """
        # if alameda
        if self.slug == constants.Counties.ALAMEDA:
            # if under 3000 and not owns home
            income = answers.get('monthly_income')
            owns_home = answers.get('owns_home')
            if income < 3000 and owns_home == field_types.NO:
                # return alameda pub def
                return self.organizations.get(
                    slug=constants.Organizations.ALAMEDA_PUBDEF)
            else:
                # return ebclc
                return self.organizations.get(
                    slug=constants.Organizations.EBCLC)
            # return first receiving agency
        return self.organizations.filter(is_receiving_agency=True).first()

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.slug, )


class FormSubmission(models.Model):

    organizations = models.ManyToManyField('user_accounts.Organization',
                                           related_name="submissions")
    applicant = models.ForeignKey('Applicant',
                                  on_delete=models.PROTECT, null=True,
                                  related_name='form_submissions')
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
    def create_for_organizations(cls, organizations, **kwargs):
        submission = cls(**kwargs)
        submission.save()
        submission.organizations.add(*organizations)
        return submission

    @classmethod
    def create_for_counties(cls, counties, **kwargs):
        if 'answers' not in kwargs:
            msg = ("'answers' are needed to infer organizations "
                   "for a form submission")
            raise MissingAnswersError(msg)
        organizations = [
            county.get_receiving_agency(kwargs['answers'])
            for county in counties
        ]
        return cls.create_for_organizations(
            organizations=organizations, **kwargs)

    @classmethod
    def mark_viewed(cls, submissions, user):
        # TODO: doesn't need to be a method here
        logs = ApplicationLogEntry.log_opened(
            [s.id for s in submissions], user)
        # send a slack notification
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=user)
        return submissions, logs

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
    def get_permitted_submissions(cls, user, ids=None, related_objects=False):
        query = cls.objects
        if related_objects:
            query = query.prefetch_related(
                'logs__user__profile__organization')
        if ids:
            query = query.filter(pk__in=ids)
        if user.is_staff:
            return query.all()
        org = user.profile.organization
        return query.filter(organizations=org)

    @classmethod
    def all_plus_related_objects(cls):
        return cls.objects.prefetch_related(
            'logs__user__profile__organization',
            'counties'
        ).all()

    @classmethod
    def get_daily_totals(cls):
        county_names = County.objects.all().values_list('name', flat=True)
        submissions = cls.objects.prefetch_related(
            'organizations', 'organizations__county').all()
        first_sub = min(submissions, key=lambda x: x.date_received)
        time_counter = timezone_utils.now()
        day_strings = []
        day_fmt = '%Y-%m-%d'
        a_day = datetime.timedelta(days=1)
        while time_counter > (first_sub.get_local_date_received() - a_day):
            day_strings.append(time_counter.strftime(day_fmt))
            time_counter -= a_day
        county_totals = {
            name: 0 for name in county_names}
        county_totals['All'] = 0
        day_totals = {day_str: county_totals.copy() for day_str in day_strings}
        for sub in submissions:
            day = sub.get_local_date_received(fmt=day_fmt)
            day_totals[day]['All'] += 1
            for org in sub.organizations.all():
                county_name = org.county.name
                day_totals[day][county_name] += 1
        for day, counts in sorted(day_totals.items(), key=lambda x: x[0]):
            yield dict(Day=day, **counts)

    def fill_pdfs(self):
        """Checks for and creates any needed `FilledPDF` objects
        """
        fillables = FillablePDF.objects.filter(organization__submissions=self)
        for fillable in fillables:
            fillable.fill_for_submission(self)

    def agency_event_logs(self, event_type):
        '''assumes that self.logs and self.logs.user are prefetched'''
        for log in self.logs.all():
            if log.user and hasattr(log.user, 'profile'):
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

    def get_local_date_received(self, fmt=None, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        local_datetime = self.date_received.astimezone(local_tz)
        if not fmt:
            return local_datetime
        return local_datetime.strftime(fmt)

    def get_contact_preferences(self):
        if 'contact_preferences' in self.answers:
            return [k for k in self.answers.get('contact_preferences', [])]
        else:
            return [
                k for k in self.answers
                if 'prefers' in k and self.answers[k]
            ]

    def get_nice_contact_preferences(self):
        preferences = [k[8:] for k in self.get_contact_preferences()]
        return [
            nice for key, nice
            in constants.CONTACT_METHOD_CHOICES
            if key in preferences]

    def get_counties(self):
        return County.objects.filter(
            organizations__submissions=self).distinct()

    def get_nice_counties(self):
        return self.get_counties().values_list('name', flat=True)

    def get_display_form_for_user(self, user):
        """
        based on user information, get the correct Form class and return it
        instantiated with the data for self
        """
        # TODO: get rid of this method, and put it elsewhere and make it right
        if not user.is_staff:
            DisplayFormClass = user.profile.get_submission_display_form()
        else:
            DisplayFormClass = display_form_selector.get_combined_form_class(
                counties=[
                    constants.Counties.SAN_FRANCISCO,
                    constants.Counties.CONTRA_COSTA,
                    constants.Counties.ALAMEDA,
                ])
        init_data = dict(
            date_received=self.get_local_date_received(),
            counties=list(self.get_counties().values_list('slug', flat=True)),
            organizations=list(
                self.organizations.values_list('name', flat=True))
        )
        init_data.update(self.answers)
        for key, value in init_data.items():
            if isinstance(value, str):
                init_data[key] = mark_safe(value)
        display_form = DisplayFormClass(init_data)
        display_form.display_only = True
        display_form.display_template_name = "formation/intake_display.jinja"
        # initiate parsing
        display_form.is_valid()
        return display_form

    def get_full_name(self):
        return '{first_name} {last_name}'.format(
            **{
                key: namify(self.answers.get(key))
                for key in ['first_name', 'last_name']
            })

    def get_formatted_address(self):
        address = self.answers.get('address', {})
        if not address:
            return ""
        return "{street}\n{city}, {state}\n{zip}".format(
            **self.answers.get('address', {}))

    def get_contact_info(self):
        """Returns a dictionary of contact information structured to be valid for
        intake.fields.ContactInfoJSONField
        """
        info = {}
        for key in self.get_contact_preferences():
            short = key[8:]
            field_name, nice, datum = constants.CONTACT_PREFERENCE_CHECKS[key]
            if short == 'snailmail':
                info[short] = self.get_formatted_address()
            else:
                info[short] = self.answers.get(field_name, '')
        return info

    def send_notification(self, notification, contact_info_key, **context):
        contact_info = self.get_contact_info()
        contact_info_used = {
            contact_info_key: contact_info[contact_info_key]
        }
        notification.send(
            to=[contact_info[contact_info_key]],
            **context
        )
        ApplicationLogEntry.log_confirmation_sent(
            submission_id=self.id, user=None, time=None,
            contact_info=contact_info_used,
            message_sent=notification.render_content_fields(**context)
        )

    def send_confirmation_notifications(self):
        contact_info = self.get_contact_info()
        errors = {}
        context = dict(
            staff_name=random.choice(constants.STAFF_NAME_CHOICES),
            name=self.answers['first_name'],
            county_names=self.get_nice_counties(),
            organizations=self.organizations.all())
        notification_settings = [
            ('email', notifications.email_confirmation,
                'long_confirmation_message'),
            ('sms', notifications.sms_confirmation,
                'short_confirmation_message')
        ]
        for key, notification, step_query_att in notification_settings:
            if key in contact_info:
                context.update(
                    next_steps=self.organizations.values_list(
                        step_query_att, flat=True))
                try:
                    self.send_notification(
                        notification, key, **context)
                except notifications.FrontAPIError as error:
                    errors[key] = error
        successes = sorted([key for key in contact_info if key not in errors])
        if successes:
            notifications.slack_confirmation_sent.send(
                submission=self,
                methods=successes)
        if errors:
            notifications.slack_confirmation_send_failed.send(
                submission=self,
                errors=errors)
        return self.confirmation_flash_messages(successes, contact_info)

    def confirmation_flash_messages(self, successes, contact_info):
        messages = []
        sent_email_message = _("We've sent you an email at {}")
        sent_sms_message = _("We've sent you a text message at {}")
        for method in successes:
            if method == 'email':
                messages.append(
                    sent_email_message.format(
                        contact_info['email']))
            if method == 'sms':
                messages.append(sent_sms_message.format(contact_info['sms']))
        return messages

    def get_transfer_action(self, request):
        other_org = request.user.profile.organization.get_transfer_org()
        if other_org:
            url = reverse(
                'intake-mark_transferred_to_other_org')
            url += "?ids={sub_id}&to_organization_id={org_id}".format(
                sub_id=self.id, org_id=other_org.id)
            if request.path != self.get_absolute_url():
                url += "&next={}".format(request.path)
            return dict(
                url=url,
                display=str(other_org))
        return None

    def get_anonymous_display(self):
        return self.anonymous_name

    def get_absolute_url(self):
        return reverse('intake-app_detail', kwargs=dict(submission_id=self.id))

    def get_external_url(self):
        return urljoin(settings.DEFAULT_HOST, self.get_absolute_url())

    def __str__(self):
        return self.get_anonymous_display()


class Applicant(models.Model):

    def log_event(self, name, data=None):
        event = ApplicationEvent(
            name=name,
            applicant=self,
            data=data or {}
        )
        event.save()
        return event


class ApplicationEvent(models.Model):

    time = models.DateTimeField(default=timezone_utils.now)
    name = models.TextField()
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.PROTECT, null=False,
                                  related_name='events')
    data = JSONField()


class ApplicationLogEntry(models.Model):
    OPENED = 1
    REFERRED = 2
    PROCESSED = 3
    DELETED = 4
    CONFIRMATION_SENT = 5
    REFERRED_BETWEEN_ORGS = 6

    EVENT_TYPES = (
        (OPENED, "opened"),
        (REFERRED, "referred"),
        (PROCESSED, "processed"),
        (DELETED, "deleted"),
        (CONFIRMATION_SENT, "sent confirmation"),
        (REFERRED_BETWEEN_ORGS, "referred to another org"),
    )

    time = models.DateTimeField(default=timezone_utils.now)
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL, null=True,
                             related_name='application_logs')
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.SET_NULL, null=True,
        related_name='logs')
    submission = models.ForeignKey(FormSubmission,
                                   on_delete=models.SET_NULL, null=True,
                                   related_name='logs')
    event_type = models.PositiveSmallIntegerField(
        choices=EVENT_TYPES)

    class Meta:
        ordering = ['-time']

    @classmethod
    def log_multiple(cls, event_type, submission_ids,
                     user, time=None, organization=None,
                     organization_id=None):
        if not time:
            time = timezone_utils.now()
        org_kwarg = dict(organization=organization)
        if not organization:
            if organization_id:
                org_kwarg = dict(organization_id=organization_id)
            elif event_type in [cls.PROCESSED, cls.OPENED, cls.DELETED]:
                org_kwarg = dict(organization=user.profile.organization)
        logs = []
        for submission_id in submission_ids:
            log = cls(
                time=time,
                user=user,
                submission_id=submission_id,
                event_type=event_type,
                **org_kwarg
            )
            logs.append(log)
        ApplicationLogEntry.objects.bulk_create(logs)
        return logs

    @classmethod
    def log_opened(cls, submission_ids, user, time=None):
        return cls.log_multiple(cls.OPENED, submission_ids, user, time)

    @classmethod
    def log_bundle_opened(cls, bundle, user, time=None):
        sub_ids = bundle.submissions.values_list('pk', flat=True)
        return cls.log_opened(sub_ids, user, time)

    @classmethod
    def log_referred(cls, submission_ids, user, time=None, organization=None):
        return cls.log_multiple(
            cls.REFERRED, submission_ids, user, time, organization)

    @classmethod
    def log_confirmation_sent(cls, submission_id, user,
                              time, contact_info=None, message_sent=''):
        if not time:
            time = timezone_utils.now()
        if not contact_info:
            contact_info = {}
        return ApplicantContactedLogEntry.objects.create(
            submission_id=submission_id,
            user=user,
            event_type=cls.CONFIRMATION_SENT,
            contact_info=contact_info,
            message_sent=message_sent)

    @classmethod
    def log_referred_from_one_org_to_another(cls, submission_id,
                                             to_organization_id, user):
        return cls.log_multiple(
            cls.REFERRED_BETWEEN_ORGS, [submission_id], user,
            organization_id=to_organization_id)[0]

    def to_org(self):
        return self.organization

    def from_org(self):
        return self.user.profile.organization


class ApplicantContactedLogEntry(ApplicationLogEntry):
    contact_info = model_fields.ContactInfoJSONField(default=dict)
    message_sent = models.TextField(blank=True)


class FillablePDF(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='pdfs/')
    translator = models.TextField()
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.CASCADE,
        related_name='pdfs',
        null=True
    )

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

    def fill_for_submission(self, submission):
        """Fills out a pdf and saves it as a FilledPDF instance

        used when saving a new submission
        used when retrieving a filled pdf if it doesn't
        """
        return FilledPDF.create_with_pdf_bytes(
            pdf_bytes=self.fill(submission),
            original_pdf=self,
            submission=submission
            )

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


class FilledPDF(models.Model):
    """A FillablePDF filled with FormSubmission data.
    """
    pdf = models.FileField(upload_to='filled_pdfs/')
    original_pdf = models.ForeignKey(
        FillablePDF,
        on_delete=models.SET_NULL,
        related_name='filled_copies',
        null=True)
    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='filled_pdfs')

    @classmethod
    def create_with_pdf_bytes(cls, pdf_bytes, original_pdf, submission):
        """Sets the contents of `self.pdf` to `bytes_`.
        """
        filename = 'filled_{0:0>4}-{1:0>6}.pdf'.format(
            original_pdf.id, submission.id)
        file_obj = SimpleUploadedFile(
            filename, pdf_bytes, content_type='application/pdf')
        instance = cls(
            pdf=file_obj,
            original_pdf=original_pdf,
            submission=submission)
        instance.save()
        return instance

    def get_absolute_url(self):
        """This is unique _to each submission_.

        URLs will need to be changed when multiple pdfs can pertain to one
        submission
        """
        return reverse(
            'intake-filled_pdf',
            kwargs=dict(submission_id=self.submission.id))


class ApplicationBundle(models.Model):
    submissions = models.ManyToManyField(FormSubmission,
                                         related_name='bundles')
    organization = models.ForeignKey('user_accounts.Organization',
                                     on_delete=models.PROTECT,
                                     related_name='bundles')
    bundled_pdf = models.FileField(upload_to='pdf_bundles/', null=True,
                                   blank=True)

    @classmethod
    def create_with_submissions(cls, submissions, skip_pdf=False, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        if submissions:
            instance.submissions.add(*submissions)
        if not skip_pdf and not instance.bundled_pdf:
            instance.build_bundled_pdf_if_necessary()
        return instance

    @classmethod
    def get_or_create_for_submissions_and_user(cls, submissions, user):
        query = cls.objects.all()
        for sub in submissions:
            query = query.filter(submissions=sub)
        if not user.is_staff:
            query = query.filter(organization=user.profile.organization)
        query = query.first()
        if not query:
            query = cls.create_with_submissions(
                submissions,
                organization=user.profile.organization)
        return query

    def should_have_a_pdf(self):
        """Returns `True` if `self.organization` has any `FillablePDF`
        """
        return bool(
            FillablePDF.objects.filter(organization__bundles=self).count())

    def get_individual_filled_pdfs(self):
        """Gets FilledPDFs from this bundle's submissions and target_org
        """
        return FilledPDF.objects.filter(
            submission__bundles=self,
            original_pdf__organization__bundles=self)

    def set_bundled_pdf_to_bytes(self, bytes_):
        """Sets the content of `self.pdf` to `bytes_`.
        """
        now_str = timezone_utils.now().strftime('%Y-%m-%d_%H:%M')
        filename = "submission_bundle_{0:0>4}-{1}.pdf".format(
            self.organization.pk, now_str)
        self.bundled_pdf = SimpleUploadedFile(
            filename, bytes_, content_type='application/pdf')

    def build_bundled_pdf_if_necessary(self):
        """Populates `self.bundled_pdf` attribute if needed

        First checks whether or not there should be a pdf. If so,
        - tries to grab filled pdfs for this bundles submissionts
        - if it needs a pdf but there weren't any pdfs, it logs an error and
          creates the necessary filled pdfs.
        - makes a filename based on the organization and current time.
        - adds the file data and saves itself.
        """
        needs_pdf = self.should_have_a_pdf()
        if not needs_pdf:
            return
        filled_pdfs = self.get_individual_filled_pdfs()
        if needs_pdf and not filled_pdfs:
            msg = "submissions for ApplicationBundle(pk={}) lack pdfs".format(
                self.pk)
            logger.error(msg)
            for submission in self.submissions.all():
                submission.fill_pdfs()
            filled_pdfs = self.get_individual_filled_pdfs()
        if len(filled_pdfs) == 1:
            self.set_bundled_pdf_to_bytes(filled_pdfs[0].pdf.read())
        else:
            self.set_bundled_pdf_to_bytes(
                get_parser().join_pdfs(
                    filled.pdf for filled in filled_pdfs))
        self.save()

    def get_pdf_bundle_url(self):
        return reverse(
            'intake-app_bundle_detail_pdf',
            kwargs=dict(bundle_id=self.id))

    def get_absolute_url(self):
        return reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=self.id))

    def get_external_url(self):
        return urljoin(settings.DEFAULT_HOST, self.get_absolute_url())
