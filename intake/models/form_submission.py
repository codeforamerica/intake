import uuid
from urllib.parse import urljoin

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone as timezone_utils
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
import intake
from intake import anonymous_names
from project.jinja2 import namify
from formation.forms import (
    display_form_selector, DeclarationLetterDisplay)
from formation.fields import MonthlyIncome, HouseholdSize, OnPublicBenefits


class MissingAnswersError(Exception):
    pass


class MissingPDFsError(Exception):
    pass


def gen_uuid():
    return uuid.uuid4().hex


class FormSubmission(models.Model):

    organizations = models.ManyToManyField(
        'user_accounts.Organization', related_name="submissions",
        through='intake.Application')
    applicant = models.ForeignKey(
        'Applicant', on_delete=models.PROTECT, null=True,
        related_name='form_submissions')
    duplicate_set = models.ForeignKey(
        'intake.DuplicateSubmissionSet', null=True,
        related_name='submissions')
    answers = JSONField()
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
                    intake.constants.Counties.SAN_FRANCISCO,
                    intake.constants.Counties.CONTRA_COSTA,
                    intake.constants.Counties.ALAMEDA,
                    intake.constants.Counties.MONTEREY,
                    intake.constants.Counties.SOLANO,
                    intake.constants.Counties.SAN_DIEGO,
                    intake.constants.Counties.SAN_JOAQUIN,
                    intake.constants.Counties.SANTA_CLARA,
                    intake.constants.Counties.FRESNO,
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
        display_form = DisplayFormClass(init_data, validate=True)
        display_form.display_only = True
        display_form.display_template_name = "formation/intake_display.jinja"
        display_form.submission = self
        show_declaration = any(self.organizations.all().values_list(
                'requires_declaration_letter', flat=True))
        if show_declaration:
            declaration_letter_form = DeclarationLetterDisplay(
                init_data, validate=True)
            return display_form, declaration_letter_form
        return display_form, None

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
            field_name, nice, datum = \
                intake.constants.CONTACT_PREFERENCE_CHECKS[key]
            if short == 'snailmail':
                info[short] = self.get_formatted_address()
            else:
                info[short] = self.answers.get(field_name, '')
        return info

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

    def get_case_printout_url(self):
        return reverse(
            'intake-case_printout', kwargs=dict(submission_id=self.id))

    def qualifies_for_fee_waiver(self):
        on_benefits = OnPublicBenefits(self.answers)
        if on_benefits.is_valid():
            if bool(on_benefits):
                return True
        is_under_threshold = None
        hh_size_field = HouseholdSize(self.answers)
        hh_income_field = MonthlyIncome(self.answers)
        if (hh_income_field.is_valid() and hh_size_field.is_valid()):
            hh_size = hh_size_field.get_display_value()
            annual_income = hh_income_field.get_current_value() * 12
            threshold = intake.constants.FEE_WAIVER_LEVELS.get(
                hh_size, intake.constants.FEE_WAIVER_LEVELS[12])
            is_under_threshold = annual_income <= threshold
        return is_under_threshold

    def __str__(self):
        return self.get_anonymous_display()


class DuplicateSubmissionSet(models.Model):

    def __str__(self):
        return "DuplicateSubmissionSet({})".format(
            self.submissions.count())

    def __repr__(self):
        return self.__str__()
