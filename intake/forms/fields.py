"""
Contains a complete list of all the field instances
that should be used by forms in intake.
"""
import copy
from collections import OrderedDict
from django.utils.translation import ugettext as _
from intake.forms import field_types
from intake.constants import COUNTY_CHOICES, CONTACT_PREFERENCE_CHOICES


# Meta fields about the application
counties = field_types.MultipleChoiceField(
    choices=COUNTY_CHOICES,
    label=_("Which counties were you arrested in?"))
how_did_you_hear = field_types.CharField(
    label=_("How did you hear about this program or website?"))
case_number = field_types.CharField(
    label=_('If you have one, what is your case number?'),
    help_text=_("If you don't have one or don't remember, that's okay."))
additional_information = field_types.CharField(
    label=_("Is there anything else you want to say?"))

# Identification questions
first_name = field_types.CharField(
    label=_('What is your first name?'))
middle_name = field_types.CharField(
    label=_('What is your middle name?'))
last_name = field_types.CharField(
    label=_('What is your last name?'))
dob = field_types.DateOfBirthMultiValueFormField()
ssn = field_types.SocialSecurityNumberField(
    help_text=_("The public defender's office will use this to get your San Francisco RAP sheet and find any convictions that can be reduced or dismissed."))


# Contact info questions
contact_preferences = field_types.MultipleChoiceField(
    choices=CONTACT_PREFERENCE_CHOICES,
    label=_('How would you like us to contact you?'),
    help_text=_('Code for America will use this to update you about your application.'))
phone_number = field_types.PhoneNumberField(
    help_text=_('Code for America and the public defender will use this to contact you about your application.'))
email = field_types.EmailField()
address = field_types.AddressMultiValueFormField()


# Case status and screening questions
us_citizen = field_types.YesNoField(
    label=_("Are you a U.S. citizen?"),
    help_text=_("The public defender handles non-citizen cases differently and has staff who can help with citizenship issues."))
being_charged = field_types.YesNoField(
    label=_("Are you currently being charged with a crime?"))
serving_sentence = field_types.YesNoField(
    label=_("Are you currently serving a sentence?"))
on_probation_parole = field_types.YesNoField(
    label=_("Are you on probation or parole?"))
where_probation_or_parole = field_types.CharField(
    label=_("Where is your probation or parole?"))
when_probation_or_parole = field_types.CharField(
    label=_("When does your probation or parole end?"))
rap_outside_sf = field_types.YesNoField(
    label=_("Have you ever been arrested or convicted outside of San Francisco?"))
when_where_outside_sf = field_types.CharField(
    label=_("When and where were you arrested or convicted outside of San Francisco?"))


# Financial questions
financial_screening_note = _("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs.")
currently_employed = field_types.YesNoField(
    label=_("Are you currently employed?"))
monthly_income = field_types.CharField(
    label=_("What is your monthly_income?"))
income_source = field_types.CharField(
    label=_("Where does your income come from?"),
    help_text=_("For example: Job, Social Security, Food stamps"))
monthly_expenses = field_types.CharField(
    label=_("How much do you spend each month on things like rent, groceries, utilities, medical expenses, or childcare expenses?"))


# This defines the order of all fields in relation to each other
INTAKE_FIELDS = [
    counties,

    contact_preferences,

    first_name,
    middle_name,
    last_name,

    phone_number,
    email,
    address,
    dob,
    ssn,

    us_citizen,
    serving_sentence,
    on_probation_parole,
    where_probation_or_parole,
    when_probation_or_parole,
    rap_outside_sf,
    when_where_outside_sf,

    financial_screening_note,
    currently_employed,
    monthly_income,
    income_source,
    monthly_expenses,

    case_number,
    how_did_you_hear,
    additional_information,
]

FIELD_NAME_LOOKUP = {}
temp_locals = copy.copy(locals())
for name, thing in temp_locals.items():
    if isinstance(thing, field_types.FormFieldMixin):
        FIELD_NAME_LOOKUP[name] = thing
