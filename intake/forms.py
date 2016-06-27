from django import forms
from django.utils.translation import ugettext as _




YES_NO_CHOICES = (
    ('yes', _('Yes')),
    ('no',  _('No')),
    )


def YesNoBlankField(**kwargs):
    """Returns a RadioSelect field with three valid options:
        'Yes', 'No', and ''
    """
    base_args = dict(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect,
        required=False)
    base_args.update(**kwargs)
    return forms.ChoiceField(**base_args)


class BaseApplicationForm(forms.Form):
    """The default application form for the SF Public Defender
        Clean Slate program.
        This should be split apart as new organization's intake forms
        are added.

    """

    CONTACT_PREFERENCE_CHOICES = (
        ('prefers_email',     _('Email')),
        ('prefers_sms',       _('Text Message')),
        ('prefers_snailmail', _('Paper mail')),
        ('prefers_voicemail', _('Voicemail')),
        )

    fieldsets = {}

    contact_preferences = forms.ChoiceField(
        label=_('How would you like us to contact you?'),
        help_text=_(
            'Code for America will use this to update you about your application.'),
        choices=CONTACT_PREFERENCE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        )

    first_name = forms.CharField(
        label=_('What is your first name?'))
    middle_name = forms.CharField(
        label=_('What is your middle name?'),
        required=False)
    last_name = forms.CharField(
        label=_('What is your last name?'))

    phone_number = forms.CharField(
        label=_('What is your phone number?'),
        help_text=_('Code for America and the public defender will use this to contact you about your application.'),
        required=False)
    email = forms.EmailField(
        label=_('What is your email?'),
        help_text=_('For example "yourname@example.com"'),
        required=False)

    # date of birth
    dob_fieldset = dict(
        label=_("What is your date of birth?"),
        help_text=_("For example: 4/28/1986"))
    dob_month = forms.CharField(
        label=_("Month"), required=False)
    dob_day = forms.CharField(
        label=_("Day"), required=False)
    dob_year = forms.CharField(
        label=_("Year"), required=False)

    ssn = forms.CharField(
        label=_('What is your Social Security Number?'),
        help_text=_("The public defender's office will use this to get your San Francisco RAP sheet and find any convictions that can be reduced or dismissed."),
        required=False)
    us_citizen = YesNoBlankField(
        label=_("Are you a U.S. citizen?"),
        help_text=_("The public defender handles non-citizen cases differently and has staff who can help with citizenship issues."))

    # mailing address
    address_fieldset = dict(
        label=_("What is your mailing address?"),
        help_text=_("The public defender will need to send you important papers."))
    address_street = forms.CharField(required=False)
    address_city = forms.CharField(
        label=_("City"), required=False)
    address_state = forms.CharField(
        label=_("State"), required=False, initial="CA")
    address_zip = forms.CharField(
        label=_("Zip code"), required=False)

    on_probation_parole = YesNoBlankField(
        label=_("Are you on probation or parole?"))
    where_probation_or_parole = forms.CharField(
        label=_("Where is your probation or parole?"),
        required=False)
    when_probation_or_parole = forms.CharField(
        label=_("When does your probation or parole end?"),
        required=False)
    serving_sentence = YesNoBlankField(
        label=_("Are you currently serving a sentence?"))
    being_charged = YesNoBlankField(
        label=_("Are you currently being charged with a crime?"))
    rap_outside_sf = YesNoBlankField(
        label=_("Have you ever been arrested or convicted outside of San Francisco?"))
    when_where_outside_sf = forms.CharField(
        label=_("When and where were you arrested or convicted outside of San Francisco?"),
        required=False)

    currently_employed = YesNoBlankField(
        label=_("Are you currently employed?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."))
    monthly_income = forms.CharField(
        label=_("What is your monthly income?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."),
        required=False)
    monthly_expenses = forms.CharField(
        label=_("How much do you spend each month on things like rent, groceries, utilities, medical expenses, or childcare expenses?"),
        help_text=_("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs."),
        required=False)

    how_did_you_hear = forms.CharField(
        label=_("How did you hear about this program or website?"),
        required=False)

    def __init__(self, *args, **kwargs):
        """Overrides default initialization to add a _warnings instance attribute
        """
        self._warnings = {}
        super().__init__(*args, **kwargs)

    def clean(self):
        """Peforms default cleaning and checks for answers that should raise warnings
        """
        cleaned_data = super().clean()
        # methods used to raise warnings
        warning_checks = [
            self.check_ssn,
            self.check_dob,
            self.check_address
        ]
        for check_method in warning_checks:
            check_method(cleaned_data)

    def add_warning(self, key, msg):
        field_warnings = self._warnings.get(key, [])
        field_warnings.append(msg)
        self._warnings[key] = field_warnings

    def check_ssn(self, data):
        if not data.get('ssn', None):
            self.add_warning('ssn',
                _("The public defender may not be able to check your RAP sheet without a social security number")
                )

    def all_keys(self, data, keys):
        return all([
            bool(data.get(key, ''))
            for key in keys
        ])

    def filled_all_dob_fields(self, data):
        return self.all_keys(data,
            [
                'dob_month',
                'dob_day',
                'dob_year'])

    def filled_all_address_fields(self, data):
        return self.all_keys(data,
            [
                'address_street',
                'address_city',
                'address_state',
                'address_zip'])

    def check_dob(self, data):
        if not self.filled_all_dob_fields(data):
            self.add_warning('dob',
                _("The public defender may not be able to check your RAP sheet without a full date of birth")
                )

    def check_address(self, data):
        if not self.filled_all_address_fields(data):
            self.add_warning('address',
                _("The public defender needs a mailing address to send you a letter with the next steps")
                )

    def should_raise_warnings(self):
        """returns True or False indicating whether or not warnings should
        be raised for the user on a confirmation submission page.
        """
        return bool(self._warnings)

    def get_warnings(self):
        return self._warnings

