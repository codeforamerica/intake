from django import forms
from django.forms.boundfield import BoundField
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
import rest_framework
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.serializers import ValidationError, get_validation_error_detail

from intake import validators, fields


YES_NO_CHOICES = (
    ('yes', _('Yes')),
    ('no',  _('No')),
    )


class Warnings:
    DOB = _("The public defender may not be able to check your RAP sheet without a full date of birth.")
    ADDRESS = _("The public defender needs a mailing address to send you a letter with the next steps.")
    SSN = _("The public defender may not be able to check your RAP sheet without a social security number.")


def YesNoBlankField(**kwargs):
    """Returns a RadioSelect field with three valid options:
        'Yes', 'No', and ''
    """
    base_args = dict(
        choices=YES_NO_CHOICES,
        required=False)
    base_args.update(**kwargs)
    return fields.ChoiceField(**base_args)


class FormSubmissionSerializer(serializers.Serializer):
    """Builds on Django REST Framework's serializers to create a Form class
        with a cleaner API than Django's default forms.
    """

    CONTACT_PREFERENCE_CHOICES = (
        ('prefers_email',     _('Email')),
        ('prefers_sms',       _('Text Message')),
        ('prefers_snailmail', _('Paper mail')),
        ('prefers_voicemail', _('Voicemail')),
        )

    contact_preferences = fields.MultipleChoiceField(
        label=_('How would you like us to contact you?'),
        help_text=_(
            'Code for America will use this to update you about your application.'),
        choices=CONTACT_PREFERENCE_CHOICES,
        required=False
        )

    first_name = fields.CharField(
        label=_('What is your first name?'))
    middle_name = fields.CharField(
        label=_('What is your middle name?'),
        required=False)
    last_name = fields.CharField(
        label=_('What is your last name?'))

    phone_number = fields.CharField(
        label=_('What is your phone number?'),
        help_text=_('Code for America and the public defender will use this to contact you about your application.'),
        required=False)
    email = fields.EmailField(
        label=_('What is your email?'),
        help_text=_('For example "yourname@example.com"'),
        required=False)

    dob = fields.DateOfBirthFieldSerializer(
        label=_("What is your date of birth?"),
        help_text=_("For example: 4/28/1986"),
        required=False)
    ssn = fields.CharField(
        label=_('What is your Social Security Number?'),
        help_text=_("The public defender's office will use this to get your San Francisco RAP sheet and find any convictions that can be reduced or dismissed."),
        required=False)

    us_citizen = YesNoBlankField(
        label=_("Are you a U.S. citizen?"),
        help_text=_("The public defender handles non-citizen cases differently and has staff who can help with citizenship issues."))

    address = fields.AddressFieldSerializer(
        label=_("What is your mailing address?"),
        help_text=_("The public defender will need to send you important papers."),
        required=False)

    on_probation_parole = YesNoBlankField(
        label=_("Are you on probation or parole?"))
    where_probation_or_parole = fields.CharField(
        label=_("Where is your probation or parole?"),
        required=False)
    when_probation_or_parole = fields.CharField(
        label=_("When does your probation or parole end?"),
        required=False)
    serving_sentence = YesNoBlankField(
        label=_("Are you currently serving a sentence?"))
    being_charged = YesNoBlankField(
        label=_("Are you currently being charged with a crime?"))
    rap_outside_sf = YesNoBlankField(
        label=_("Have you ever been arrested or convicted outside of San Francisco?"))
    when_where_outside_sf = fields.CharField(
        label=_("When and where were you arrested or convicted outside of San Francisco?"),
        required=False)

    currently_employed = YesNoBlankField(
        label=_("Are you currently employed?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."))
    monthly_income = fields.CharField(
        label=_("What is your monthly income?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."),
        required=False)
    monthly_expenses = fields.CharField(
        label=_("How much do you spend each month on things like rent, groceries, utilities, medical expenses, or childcare expenses?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."),
        required=False)

    how_did_you_hear = fields.CharField(
        label=_("How did you hear about this program or website?"),
        required=False)

    class Meta:
        validators = [
            validators.gave_preferred_contact_methods
        ]

    def __init__(self, data=None, **kwargs):
        if data is None:
            data = {}
        kwargs['data'] = data
        # toss out the extra kwargs given by django's class-based views
        kwargs = {
            k: v for k, v in kwargs.items()
            if k in serializers.LIST_SERIALIZER_KWARGS}
        super().__init__(**kwargs)
        self.warnings = {}

    def add_warning(self, key, msg):
        field_warnings = self.warnings.get(key, [])
        field_warnings.append(msg)
        self.warnings[key] = field_warnings

    def non_field_errors(self):
        return self.errors.get('non_field_errors', [])

    def validate_address(self, address):
        if not address:
            self.add_warning('address', Warnings.ADDRESS)
        return address

    def validate_ssn(self, ssn):
        if not ssn.strip():
            self.add_warning('ssn', Warnings.SSN)
        return ssn

    def validate_dob(self, dob):
        if not dob:
            self.add_warning('dob', Warnings.DOB)
        return dob

    def run_validation(self, data=rest_framework.fields.empty):
        """Overrides rest_framework.serializers.Serializer.run_validation
            in order to report errors at both the field level and the
            serializer level.
            In the parent class, if field-level errors were raised, then
            serializer-level errors were not reported
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data
        errors = {}
        value = data

        try:
            value = self.to_internal_value(data)
        except (ValidationError, DjangoValidationError) as exc:
            errors.update(get_validation_error_detail(exc))

        try:
            self.run_validators(value)
            value = self.validate(value)
            assert value is not None, '.validate() should return the validated data'
        except (ValidationError, DjangoValidationError) as exc:
            errors.update(get_validation_error_detail(exc))

        if errors:
            raise ValidationError(detail=errors)
        return value


