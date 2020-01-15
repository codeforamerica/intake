import uuid
from urllib.parse import urljoin
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone as timezone_utils
from django.urls import reverse
from taggit.managers import TaggableManager
from dateutil.parser import parse
import intake
from intake import anonymous_names
from intake.constants import SMS, EMAIL
from project.jinja2 import namify


FORMSUBMISSION_TEXT_SEARCH_FIELDS = [
    'first_name',
    'last_name',
    'ssn',
    'last_four',
    'drivers_license_or_id',
    'case_number',
    'phone_number',
    'alternate_phone_number',
    'email'
]

QUERYABLE_ANSWER_FIELDS = [
    'reasons_for_applying',
    'how_did_you_hear',
    'additional_information',
    'aliases',
    'pfn_number',
    'contact_preferences',
    'preferred_pronouns',
    'street',
    'city',
    'state',
    'zip',
    'us_citizen',
    'is_veteran',
    'is_student',
    'being_charged',
    'serving_sentence',
    'on_probation_parole',
    'where_probation_or_parole',
    'when_probation_or_parole',
    'finished_half_probation',
    'reduced_probation',
    'rap_outside_sf',
    'when_where_outside_sf',
    'has_suspended_license',
    'owes_court_fees',
    'currently_employed',
    'income_source',
    'on_public_benefits',
    'owns_home',
    'household_size',
    'dependents',
    'is_married',
    'has_children',
    'unlisted_counties'
]


DOLLAR_FIELDS = [
    'monthly_income',
    'monthly_expenses'
]

"""
Some fields were not extracted from the answers blob;
UNEXTRACTED FIELDS = [
    'consent_to_represent',
    'consent_self_represent',
    'understands_limits',
    'address',
    'declaration_letter_note',
    'declaration_letter_intro',
    'declaration_letter_life_changes',
    'declaration_letter_activities',
    'declaration_letter_goals',
    'declaration_letter_why'
    ]
"""


class MissingAnswersError(Exception):
    pass


class MissingPDFsError(Exception):
    pass


def gen_uuid():
    return uuid.uuid4().hex


class PurgedFormSubmission(models.Model):
    """Placeholder for custom VIEW see intake migration 0061
    Its possible to make an abstract Model from FormSubmission and
    subclass here and in FormSubmission if we want to be able to
    use the ORM
    """
    class Meta:
        db_table = 'purged\".\"intake_formsubmission'
        managed = False


class FormSubmission(models.Model):

    text_search_fields = FORMSUBMISSION_TEXT_SEARCH_FIELDS
    answer_fields = (
        FORMSUBMISSION_TEXT_SEARCH_FIELDS +
        QUERYABLE_ANSWER_FIELDS + DOLLAR_FIELDS)

    organizations = models.ManyToManyField(
        'user_accounts.Organization', related_name="submissions",
        through='intake.Application')
    applicant = models.ForeignKey(
        'Applicant', on_delete=models.PROTECT, null=True,
        related_name='form_submissions')
    duplicate_set = models.ForeignKey(
        'intake.DuplicateSubmissionSet', models.PROTECT, null=True,
        related_name='submissions')
    answers = JSONField()
    has_been_sent_followup = models.BooleanField(default=False)

    # extracting these values from answers for autocomplete/search/querying
    first_name = models.TextField(default="")
    last_name = models.TextField(default="")
    dob = models.DateField(null=True)
    ssn = models.TextField(default="")
    last_four = models.TextField(default="")
    drivers_license_or_id = models.TextField(default="")
    case_number = models.TextField(default="")
    phone_number = models.TextField(default="")
    alternate_phone_number = models.TextField(default="")
    email = models.TextField(default="")
    reasons_for_applying = models.TextField(default="")
    how_did_you_hear = models.TextField(default="")
    additional_information = models.TextField(default="")
    aliases = models.TextField(default="")
    pfn_number = models.TextField(default="")
    contact_preferences = models.TextField(default="")
    preferred_pronouns = models.TextField(default="")
    street = models.TextField(default="")
    city = models.TextField(default="")
    state = models.TextField(default="")
    zip = models.TextField(default="")
    us_citizen = models.TextField(default="")
    is_veteran = models.TextField(default="")
    is_student = models.TextField(default="")
    being_charged = models.TextField(default="")
    serving_sentence = models.TextField(default="")
    on_probation_parole = models.TextField(default="")
    where_probation_or_parole = models.TextField(default="")
    when_probation_or_parole = models.TextField(default="")
    finished_half_probation = models.TextField(default="")
    reduced_probation = models.TextField(default="")
    rap_outside_sf = models.TextField(default="")
    when_where_outside_sf = models.TextField(default="")
    has_suspended_license = models.TextField(default="")
    owes_court_fees = models.TextField(default="")
    currently_employed = models.TextField(default="")
    monthly_income = models.IntegerField(null=True)
    income_source = models.TextField(default="")
    on_public_benefits = models.TextField(default="")
    owns_home = models.TextField(default="")
    monthly_expenses = models.IntegerField(null=True)
    household_size = models.IntegerField(null=True)
    dependents = models.TextField(default="")
    is_married = models.TextField(default="")
    has_children = models.TextField(default="")
    unlisted_counties = models.TextField(default="")

    # old_uuid is only used for porting legacy applications
    old_uuid = models.CharField(max_length=34, unique=True,
                                default=gen_uuid)
    anonymous_name = models.CharField(max_length=60,
                                      default=anonymous_names.generate)
    date_received = models.DateTimeField(default=timezone_utils.now)
    tags = TaggableManager(through='intake.SubmissionTagLink')

    class Meta:
        ordering = ['-date_received']

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
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.OPENED, min)

    def last_opened_by_agency(self):
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.OPENED, max)

    def last_processed_by_agency(self):
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.PROCESSED, max)

    def get_local_date_received(self, fmt=None, timezone_name='US/Pacific'):
        return intake.utils.local_time(
            self.date_received, fmt, timezone_name)

    def set_dob_from_answers(self):
        dob_obj = self.answers.get('dob')
        if dob_obj:
            all_values_present = all([
                dob_obj.get(key) for key in ['year', 'month', 'day']])
            if all_values_present:
                self.dob = parse(
                    ("{year}-{month}-{day}").format(year=dob_obj['year'],
                                                    month=dob_obj['month'],
                                                    day=dob_obj['day']))

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
            in intake.constants.CONTACT_METHOD_CHOICES
            if key in preferences]

    def get_counties(self):
        return intake.models.County.objects.filter(
            organizations__submissions=self).distinct()

    def get_nice_counties(self):
        return self.get_counties().values_list('name', flat=True)

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
        if not any(address.values()):
            return ""
        return "{street}\n{city}, {state}\n{zip}".format(
            **self.answers.get('address', {}))

    def get_contact_info(self):
        """Returns a dictionary of contact information structured to
        be valid for intake.fields.ContactInfoJSONField
        """
        info = {}
        for key in intake.constants.CONTACT_PREFERENCE_CHECKS:
            short = key[8:]
            field_name, nice, datum = \
                intake.constants.CONTACT_PREFERENCE_CHECKS[key]
            value = ''
            if short == 'snailmail':
                value = self.get_formatted_address()
            else:
                value = self.answers.get(field_name, '')
            if value:
                info[short] = value
        return info

    def get_preferred_contact_info(self):
        all_mediums = self.get_contact_info()
        preferred_short_codes = [
            key[8:]
            for key in self.answers.get('contact_preferences', [])]
        return {
            key: value
            for key, value in all_mediums.items()
            if key in preferred_short_codes}

    def get_usable_contact_info(self):
        return {
            key: value
            for key, value in self.get_preferred_contact_info().items()
            if key in [SMS, EMAIL]}

    def get_transfer_action(self, request):
        other_org = request.user.profile.organization.transfer_partners.first()
        if other_org:
            url = reverse(
                'intake-transfer_application',
                kwargs=dict(submission_id=self.id))
            if request.path != self.get_absolute_url():
                url += "?next={}".format(request.path)
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

    def get_external_history_url(self):
        return urljoin(
            settings.DEFAULT_HOST, reverse(
                'intake-app_history', kwargs=dict(submission_id=self.id)))

    def get_case_printout_url(self):
        return reverse(
            'intake-case_printout', kwargs=dict(submission_id=self.id))

    def get_filled_pdf_url(self):
        return reverse(
            'intake-filled_pdf', kwargs=dict(submission_id=self.id))

    def get_edit_url(self):
        return reverse(
            'intake-app_edit', kwargs=dict(submission_id=self.id))

    def get_case_update_status_url(self):
        return reverse(
            'intake-create_status_update', kwargs=dict(submission_id=self.id))

    def get_uuid(self):
        """returns the _applicant/visitor_ uuid for funnel tracking"""
        return self.applicant.get_uuid()

    def __str__(self):
        return self.get_anonymous_display()


class DuplicateSubmissionSet(models.Model):

    def __str__(self):
        return "DuplicateSubmissionSet({})".format(
            self.submissions.count())

    def __repr__(self):
        return self.__str__()
