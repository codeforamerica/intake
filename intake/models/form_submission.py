import uuid
import datetime
import random
from urllib.parse import urljoin
from pytz import timezone

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone as timezone_utils
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

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
        logs = intake.models.ApplicationLogEntry.log_opened(
            [s.id for s in submissions], user)
        # send a slack notification
        intake.notifications.slack_submissions_viewed.send(
            submissions=submissions, user=user)
        return submissions, logs

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
        county_names = intake.models.County.objects.all(
            ).values_list('name', flat=True)
        submissions = cls.objects.prefetch_related(
            'organizations', 'organizations__county').all()
        first_sub = min(submissions, key=lambda x: x.date_received)
        time_counter = timezone_utils.now().astimezone(
            intake.constants.PACIFIC_TIME)
        day_strings = []
        day_fmt = '%Y-%m-%d'
        a_day = datetime.timedelta(days=1)
        while time_counter >= (first_sub.get_local_date_received() - a_day):
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
        fillables = intake.models.FillablePDF.objects.filter(
            organization__submissions=self)
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
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.OPENED, min)

    def last_opened_by_agency(self):
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.OPENED, max)

    def last_processed_by_agency(self):
        return self.agency_log_time(
            intake.models.ApplicationLogEntry.PROCESSED, max)

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
        show_declaration = \
            user.profile.organization.requires_declaration_letter or \
            (user.is_staff and any(self.organizations.all().values_list(
                'requires_declaration_letter', flat=True)))
        if show_declaration:
            declaration_letter_form = DeclarationLetterDisplay(init_data)
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

    def send_notification(self, notification, contact_info_key, **context):
        contact_info = self.get_contact_info()
        contact_info_used = {
            contact_info_key: contact_info[contact_info_key]
        }
        notification.send(
            to=[contact_info[contact_info_key]],
            **context
        )
        intake.models.ApplicationLogEntry.log_confirmation_sent(
            submission_id=self.id, user=None, time=None,
            contact_info=contact_info_used,
            message_sent=notification.render_content_fields(**context)
        )

    def send_confirmation_notifications(self):
        contact_info = self.get_contact_info()
        errors = {}
        context = dict(
            staff_name=random.choice(intake.constants.STAFF_NAME_CHOICES),
            name=self.answers['first_name'],
            county_names=self.get_nice_counties(),
            organizations=self.organizations.all())
        notification_settings = [
            ('email', intake.notifications.email_confirmation,
                'long_confirmation_message'),
            ('sms', intake.notifications.sms_confirmation,
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
                except intake.notifications.FrontAPIError as error:
                    errors[key] = error
        successes = sorted([key for key in contact_info if key not in errors])
        if successes:
            intake.notifications.slack_confirmation_sent.send(
                submission=self,
                methods=successes)
        if errors:
            intake.notifications.slack_confirmation_send_failed.send(
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
