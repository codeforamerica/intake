
from django.utils.translation import ugettext_lazy as _
from django.core.validators import EmailValidator
from formation.field_types import (
     CharField, ChoiceField, YesNoField,
     MultipleChoiceField, MultiValueField,
     FormNote
     )
from intake.constants import COUNTY_CHOICES, CONTACT_PREFERENCE_CHOICES
from project.jinja2 import namify

###
### Meta fields about the application
###

class Counties(MultipleChoiceField):
    context_key = "counties"
    choices = COUNTY_CHOICES
    label = _('Which counties were you arrested in?')
    help_text = _("We will send your Clear My Record application to these counties.")
    display_label = "Wants help with record in"


class HowDidYouHear(CharField):
    context_key = "how_did_you_hear"
    label = _("How did you hear about this program or website?")
    display_label = "How they found out about this"


class AdditionalInformation(CharField):
    context_key = "additional_information"
    label = _("Is there anything else you want to say?")


###
### Identification Questions
###

class NameField(CharField):
    def display_value(self):
        return namify(self.get_current_value())

class FirstName(NameField):
    context_key = "first_name"
    label = _('What is your first name?')


class MiddleName(NameField):
    context_key = "middle_name"
    label = _('What is your middle name?')


class LastName(NameField):
    context_key = "last_name"
    label = _('What is your last name?')


class Month(CharField):
    context_key = "month"
    label = _("Month")

class Day(CharField):
    context_key = "day"
    label = _("Day")

class Year(CharField):
    context_key = "year"
    label = _("Year")


class DateOfBirthField(MultiValueField):
    context_key = "dob"
    label = _("What is your date of birth?")
    help_text = _("For example: 4/28/1986")
    is_required_error_message = _("The public defender may not be able to check your RAP sheet without a full date of birth.")
    is_recommended_error_message = is_required_error_message
    subfields = [
        Month,
        Day,
        Year
    ]
    display_label = "Date of birth"

    def get_display_value(self):
        return "{month}/{day}/{year}".format(**self.get_current_value())



class SocialSecurityNumberField(CharField):
    context_key = "ssn"
    label = _('What is your Social Security Number?')
    help_text = help_text=_("The public defender's office will use this to get your San Francisco RAP sheet and find any convictions that can be reduced or dismissed.")
    is_required_error_message = _("The public defender may not be able to check your RAP sheet without a social security number.")
    is_recommended_error_message = is_required_error_message
    display_label = "SSN"


###
### Contact Info Questions
###

class ContactPreferences(MultipleChoiceField):
    context_key = "contact_preferences"
    choices = CONTACT_PREFERENCE_CHOICES
    label = _('How would you like us to contact you?')
    help_text = _('Code for America will use this to update you about your application.')


class PhoneNumberField(CharField):
    context_key = "phone_number"
    label= _('What is your phone number?')


class EmailField(CharField):
    context_key = "email"
    label =_ ('What is your email?')
    help_text = _('For example "yourname@example.com"')
    validators = [
        EmailValidator(_("Please enter a valid email")),
        ]

class Street(CharField):
    context_key = "street"

class City(CharField):
    context_key = "city"
    label = _("City")

class State(CharField):
    context_key = "state"
    label = _("State")

class Zip(CharField):
    context_key = "zip"
    label = _("Zip")


class AddressField(MultiValueField):
    context_key = "address"
    label = _("What is your mailing address?")
    help_text = _("")
    template_name = "formation/multivalue_address.jinja"
    is_required_error_message = _("The public defender needs a mailing address to send you a letter with the next steps.")
    is_recommended_error_message = is_required_error_message
    subfields = [
        Street,
        City,
        State,
        Zip
    ]
    display_template_name = "formation/address_display.jinja"

    def get_display_value(self):
        return "{street}\n{city}, {state}\n{zip}".format(**self.get_current_value())


###
### Case status and screening
###

class USCitizen(YesNoField):
    context_key = "us_citizen"
    label = _("Are you a U.S. citizen?")
    help_text = _("The public defender handles non-citizen cases differently and has staff who can help with citizenship issues.")
    display_label = "Is a citizen"


class BeingCharged(YesNoField):
    context_key = "being_charged"
    label = _("Are you currently being charged with a crime?")
    display_label = "Is currently being charged"


class ServingSentence(YesNoField):
    context_key = "serving_sentence"
    label = _("Are you currently serving a sentence?")
    display_label = "Is serving a sentence"


class OnProbationParole(YesNoField):
    context_key = "on_probation_parole"
    label = _("Are you on probation or parole?")
    display_label = "Is on probation or parole"

class WhereProbationParole(CharField):
    context_key = "where_probation_or_parole"
    label = _("Where is your probation or parole?")
    display_label = "Probation/Parole location"


class WhenProbationParole(CharField):
    context_key = "when_probation_or_parole"
    label = _("When does your probation or parole end?")
    display_label = "Probation/Parole ends"


class RAPOutsideSF(YesNoField):
    context_key = "rap_outside_sf"
    label = _("Have you ever been arrested or convicted outside of San Francisco?")
    display_label = "Has RAP outside SF"


class WhenWhereOutsideSF(CharField):
    context_key = "when_where_outside_sf"
    label = _("When and where were you arrested or convicted outside of San Francisco?")
    display_label = "Convictions/arrests outside SF"


###
### Financial Questions
###


class FinancialScreeningNote(FormNote):
    context_key = "financial_screening_note"
    content = _("The Clean Slate program is free for you, but the public defender uses this information to get money from government programs.")


class CurrentlyEmployed(YesNoField):
    context_key = "currently_employed"
    label = _("Are you currently employed?")
    display_label = "Is employed"


class MonthlyIncome(CharField):
    context_key = "monthly_income"
    label = _("What is your monthly income?")


class IncomeSource(CharField):
    context_key = "income_source"
    label = _("Where does your income come from?")
    help_text = _("For example: Job, Social Security, Food stamps")


class MonthlyExpenses(CharField):
    context_key = "monthly_expenses"
    label = _("How much do you spend each month on things like rent, groceries, utilities, medical expenses, or childcare expenses?")


INTAKE_FIELDS = [
    Counties,

    ContactPreferences,

    FirstName,
    MiddleName,
    LastName,

    PhoneNumberField,
    EmailField,
    AddressField,
    DateOfBirthField,
    SocialSecurityNumberField,

    USCitizen,
    BeingCharged,
    ServingSentence,
    OnProbationParole,
    WhereProbationParole,
    WhenProbationParole,
    RAPOutsideSF,
    WhenWhereOutsideSF,

    FinancialScreeningNote,
    CurrentlyEmployed,
    MonthlyIncome,
    IncomeSource,
    MonthlyExpenses,

    HowDidYouHear,
    AdditionalInformation,
]



FIELD_NAME_LOOKUP = {
    c.context_key: c for c in INTAKE_FIELDS
}

def get_field_index(field):
    return INTAKE_FIELDS.index(field)


