from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.core.validators import EmailValidator
from formation.field_types import (
    CharField, MultilineCharField, IntegerField, WholeDollarField, ChoiceField,
    YesNoField, MultipleChoiceField, MultiValueField,
    FormNote, DateTimeField, YES_NO_CHOICES, NOT_APPLICABLE
)
from intake.constants import (
    COUNTY_CHOICES, CONTACT_PREFERENCE_CHOICES,
    GENDER_PRONOUN_CHOICES,
    COUNTY_CHOICE_DISPLAY_DICT
)
from project.jinja2 import namify

###
# Meta fields about the application
###


class DateReceived(DateTimeField):
    context_key = "date_received"
    default_display_format = "%b %-d, %Y"
    display_label = "Applied on"

    def get_display_value(self):
        value = super().get_display_value()
        if value:
            local_now = timezone.now()
            time_delta = local_now - self.get_current_value()
            n_days = abs(time_delta.days)
            if n_days == 0:
                note = " (today)"
            else:
                note = " ({} day{} ago)".format(
                    n_days,
                    's' if n_days != 1 else '')
            value = value + note
        return value


class Counties(MultipleChoiceField):
    context_key = "counties"
    choices = COUNTY_CHOICES
    label = _('Where would you like to apply for help with your arrests or '
              'convictions?')
    help_text = _(
        "We will send your Clear My Record application to these counties.")
    display_label = "Wants help with record in"
    choice_display_dict = COUNTY_CHOICE_DISPLAY_DICT


class ConsentNote(FormNote):
    context_key = "consent_note"
    content = mark_safe("""
    <p>
      By clicking "Apply",  you are:
    </p>
    <ol>
      <li>
        Giving attorneys in the county you are applying in the permission to
        request your criminal record (RAP sheet).
      </li>
      <li>
        Acknowledging that filling out this form is not a guarantee that an
        attorney will represent you.
      </li>
    </ol>""")


class HowDidYouHear(CharField):
    context_key = "how_did_you_hear"
    label = _("How did you hear about this program or website?")
    display_label = "How they found out about this"


class AdditionalInformation(CharField):
    context_key = "additional_information"
    label = _("Is there anything else you would like us to know?")


###
# Identification Questions
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
    is_required_error_message = _("The public defender may not be able to "
                                  "check your RAP sheet without a full date "
                                  "of birth.")
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
    help_text = help_text = _("The public defender's office will use this to "
                              "get your San Francisco RAP sheet and find any "
                              "convictions that can be reduced or dismissed.")
    is_required_error_message = _("The public defender may not be able to "
                                  "check your RAP sheet without a social "
                                  "security number.")
    is_recommended_error_message = is_required_error_message
    display_label = "SSN"


###
# Contact Info Questions
###

class ContactPreferences(MultipleChoiceField):
    context_key = "contact_preferences"
    choices = CONTACT_PREFERENCE_CHOICES
    label = _('How would you like us to contact you?')
    help_text = _('Code for America will use this to update you about '
                  'your application.')
    display_label = "Prefers contact via"

    def get_display_value(self):
        return super().get_display_value(use_or=True)


class PreferredPronouns(ChoiceField):
    context_key = "preferred_pronouns"
    choices = GENDER_PRONOUN_CHOICES
    label = _('How would you like us to address you?')
    display_label = "Preferred pronouns"


class PhoneNumberField(CharField):
    context_key = "phone_number"
    label = _('What is your phone number?')


class AlternatePhoneNumberField(CharField):
    context_key = "alternate_phone_number"
    label = _('Do you have another phone number we can try?')


class EmailField(CharField):
    context_key = "email"
    label = _('What is your email?')
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
    is_required_error_message = _("The public defender needs a mailing "
                                  "address to send you a letter with the next "
                                  "steps.")
    is_recommended_error_message = is_required_error_message
    subfields = [
        Street,
        City,
        State,
        Zip
    ]
    display_template_name = "formation/address_display.jinja"

    def get_display_value(self):
        return "{street}\n{city}, {state}\n{zip}".format(
            **self.get_current_value())


###
# Case status and screening
###

class USCitizen(YesNoField):
    context_key = "us_citizen"
    label = _("Are you a U.S. citizen?")
    help_text = _(
        "It is important for your attorney to know if you are a "
        "U.S citizen so they can find the best ways to help you.")
    display_label = "Is a citizen"


class BeingCharged(YesNoField):
    context_key = "being_charged"
    label = _("Are you currently being charged with a crime?")
    display_label = "Is currently being charged"
    flip_display_choice_order = True


class ServingSentence(YesNoField):
    context_key = "serving_sentence"
    label = _("Are you currently serving a sentence?")
    display_label = "Is serving a sentence"
    flip_display_choice_order = True


class OnProbationParole(YesNoField):
    context_key = "on_probation_parole"
    label = _("Are you on probation or parole?")
    display_label = "Is on probation or parole"
    flip_display_choice_order = True


class WhereProbationParole(CharField):
    context_key = "where_probation_or_parole"
    label = _("Where is your probation or parole?")
    display_label = "Where"


class WhenProbationParole(CharField):
    context_key = "when_probation_or_parole"
    label = _("When does your probation or parole end?")
    display_label = "Until"


class FinishedHalfProbation(ChoiceField):
    context_key = "finished_half_probation"
    choices = YES_NO_CHOICES + ((NOT_APPLICABLE, _("Not on probation")),)
    label = _("If you're on probation, have you finished half of your "
              "probation time?")
    display_label = "Finished half probation"

    def render(self, display=False, **extra_context):
        if self.get_current_value() != NOT_APPLICABLE:
            self.display_template_name = "formation/option_set_display.jinja"
        return super().render(display, **extra_context)

    def get_display_choices(self):
        return YES_NO_CHOICES


class ReducedProbation(FinishedHalfProbation):
    context_key = "reduced_probation"
    label = _("If you're on probation, has the judge promised to reduce your "
              "probation time or end your probation early?")
    display_label = "Reduced probation"


class RAPOutsideSF(YesNoField):
    context_key = "rap_outside_sf"
    label = _("Have you ever been arrested or convicted outside of San "
              "Francisco?")
    display_label = "Has RAP outside SF"
    flip_display_choice_order = True


class WhenWhereOutsideSF(CharField):
    context_key = "when_where_outside_sf"
    label = _("When and where were you arrested or convicted outside of San "
              "Francisco?")
    display_label = "Where/when"


###
# Financial Questions
###


class FinancialScreeningNote(FormNote):
    context_key = "financial_screening_note"
    content = _("Clean Slate uses information about your income to "
                "give low income applicants special help and get help from "
                "government programs.")


class CurrentlyEmployed(YesNoField):
    context_key = "currently_employed"
    label = _("Are you currently employed?")
    display_label = "Is employed"


class IsReasonableMonthsWages:
    amount_warning = _("Are you sure {} is the right amount per month ?")

    def __init__(self, bottom, top, zero_okay=True):
        self.interval = (bottom, top)
        self.zero_okay = zero_okay

    def set_context(self, field):
        self.field = field

    def __call__(self, value):
        bottom, top = self.interval
        if self.zero_okay and value == 0:
            return
        if not (bottom < value < top):
            self.field.add_warning(
                self.amount_warning.format(
                    self.field.get_display_value())
                )


class MonthlyIncome(WholeDollarField):
    context_key = "monthly_income"
    label = _("What is your monthly household income?")
    help_text = _("Enter '0' if you have no income. "
                  "Your best estimate is okay.")
    validators = [
        IsReasonableMonthsWages(10, 10000),
    ]


class IncomeSource(CharField):
    context_key = "income_source"
    label = _("Where does your income come from?")
    help_text = _("For example: Job, Social Security, Food stamps")


class OnPublicBenefits(YesNoField):
    context_key = "on_public_benefits"
    label = _("Are you on any government benefits?")


class OwnsHome(YesNoField):
    context_key = "owns_home"
    label = _("Do you own your home?")


class MonthlyExpenses(WholeDollarField):
    context_key = "monthly_expenses"
    help_text = _("Your best estimate is okay.")
    label = _("How much do you spend each month on things like rent, "
              "groceries, utilities, medical expenses, or childcare expenses?")


class HouseholdSize(IntegerField):
    context_key = "household_size"
    label = _("How many people live with you?")
    help_text = _('For example: "3" or "0"')

    def get_display_value(self):
        """The question asks for people in addition to the applicant but
        reviewers typically want to see the applicant included in the number.
        """
        value = self.get_current_value()
        if value is not None:
            value += 1
        return value


###
# Declaration Letter
###

class AlamedaDeclarationLetterNote(FormNote):
    context_key = "alameda_declaration_letter_note"
    content = _("Create your letter for the Alameda County Judge. This is "
                "required to complete your appication in Alameda County.")


class DeclarationLetterIntro(MultilineCharField):
    context_key = "declaration_letter_intro"
    label = _("Introduce yourself. What has been going on in your life?")
    help_text = _("Write your answer in 3-5 sentences. The judge will read "
                  "this when deciding whether to clear your record.")


class DeclarationLetterLifeChanges(DeclarationLetterIntro):
    context_key = "declaration_letter_life_changes"
    label = _("How is your life different now, since your last conviction?")


class DeclarationLetterActivities(DeclarationLetterIntro):
    context_key = "declaration_letter_activities"
    label = _("Have you been involved in jobs, programs, activities, or "
              "community service? What were they and what did you do?")


class DeclarationLetterGoals(DeclarationLetterIntro):
    context_key = "declaration_letter_goals"
    label = _("What goals are you working on achieving in your life right "
              "now? How are you working on them?")


class DeclarationLetterWhy(DeclarationLetterIntro):
    context_key = "declaration_letter_why"
    label = _("Why do you want to clear your record? How will this change or "
              "help your life?")


INTAKE_FIELDS = [
    DateReceived,
    Counties,

    ContactPreferences,

    FirstName,
    MiddleName,
    LastName,

    PreferredPronouns,

    PhoneNumberField,
    AlternatePhoneNumberField,
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
    FinishedHalfProbation,
    ReducedProbation,
    RAPOutsideSF,
    WhenWhereOutsideSF,

    FinancialScreeningNote,
    CurrentlyEmployed,
    MonthlyIncome,
    IncomeSource,
    OnPublicBenefits,
    MonthlyExpenses,
    OwnsHome,
    HouseholdSize,

    HowDidYouHear,
    AdditionalInformation,
    ConsentNote,

    AlamedaDeclarationLetterNote,
    DeclarationLetterIntro,
    DeclarationLetterLifeChanges,
    DeclarationLetterActivities,
    DeclarationLetterGoals,
    DeclarationLetterWhy,
]


FIELD_NAME_LOOKUP = {
    c.context_key: c for c in INTAKE_FIELDS
}


def get_field_index(field):
    return INTAKE_FIELDS.index(field)
