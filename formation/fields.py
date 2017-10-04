from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.core.validators import (
    EmailValidator, URLValidator, RegexValidator, MinValueValidator,
    MaxValueValidator)
from formation.validators import mailgun_email_validator
from intake.models import County
from formation.field_types import (
    CharField, MultilineCharField, IntegerField, WholeDollarField, ChoiceField,
    YesNoField, YesNoIDontKnowField, MultipleChoiceField, MultiValueField,
    PhoneField, FormNote, DateTimeField, ConsentCheckbox,
    YES_NO_CHOICES, NOT_APPLICABLE, YES_NO_IDK_CHOICES
)
from intake.constants import (
    CONTACT_PREFERENCE_CHOICES, REASON_FOR_APPLYING_CHOICES,
    GENDER_PRONOUN_CHOICES, DECLARATION_LETTER_REVIEW_CHOICES,
    APPLICATION_REVIEW_CHOICES
)
from project.jinja2 import namify, oxford_comma

###
# Meta fields about the application
###


class DateReceived(DateTimeField):
    context_key = "date_received"
    default_display_format = "%b %-d, %Y"
    display_label = "Applied on"

    def get_display_value(self, strftime_format=None):
        value = super().get_display_value(strftime_format=strftime_format)
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
        return mark_safe(value)


class Counties(MultipleChoiceField):
    template_name = "formation/counties_input.jinja"
    display_template_name = "formation/counties_display.jinja"
    context_key = "counties"
    label = _('Where were you arrested or convicted?')
    help_text = _(
        "We will send your Clear My Record application to agencies in these "
        "counties.")
    display_label = "Wants help with record in"

    def __init__(self, *args, **kwargs):
        # prevents the choices query from being called during import
        self.valid_choices = County.objects.get_county_choices()
        self.possible_choices = \
            County.objects.get_all_counties_as_choice_list()
        self.choices = self.valid_choices
        super().__init__(*args, **kwargs)

    def get_ordered_selected_counties(self):
        selected_counties = self.get_current_value()
        return [
            county for county_slug, county in self.possible_choices
            if county_slug in selected_counties]

    def get_display_for_county(self, county, unlisted_counties=None):
        if (county.slug == 'not_listed') and unlisted_counties:
                return '“{}”'.format(unlisted_counties)
        return county.name

    def get_display_value(self, unlisted_counties=None):
        return oxford_comma([
            self.get_display_for_county(county, unlisted_counties)
            for county in self.get_ordered_selected_counties()])


class UnlistedCountyNote(FormNote):
    context_key = "unlisted_county_note"
    content = mark_safe("""
    <p>
        In counties where we don't have official partners, we will send you
        information on how to get started.
    </p>
    """)


class UnlistedCounties(CharField):
    context_key = "unlisted_counties"
    label = _(
        "Which counties were not listed that you need to clear your record in?"
    )
    display_label = "Needs help in unlisted counties"


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


class ConsentToRepresent(ConsentCheckbox):
    context_key = "consent_to_represent"
    is_required_error_message = (
        "The attorneys need your permission in order to help you")
    label = _(
        "Is it okay for attorneys in each county you've selected to access "
        "your criminal record, file petitions for you, and attend court on "
        "your behalf, even if you aren't there?")
    agreement_text = _("Yes, I give them permission to do that")
    display_label = str(
        "Consents to record access, filing, and court representation")


class UnderstandsLimits(ConsentCheckbox):
    context_key = "understands_limits"
    is_required_error_message = (
        "We need your understanding before we can help you")
    label = _(
        "Do you understand that not everyone qualifies for help, submitting "
        "this form does not guarantee that you will be represented by one of "
        "our partners, and it might take a few months to finish?")
    agreement_text = _("Yes, I understand")
    display_label = str(
        "Understands might not qualify and could take a few months")


class IdentityConfirmation(ConsentCheckbox):
    context_key = "identity_confirmation"
    is_required_error_message = (
        "We need your understanding before we can help you")
    label = _(
        "Do you understand that this application should only be submitted for "
        "yourself or someone who has given you permission to apply on their "
        "behalf, and that it is illegal to use this application to gain "
        "access to someone's private information?")
    agreement_text = _("Yes, I understand")
    display_label = str(
        "Confirms application is for self or with permission")


class UnderstandsMaybeFee(ConsentCheckbox):
    context_key = "understands_maybe_fee"
    is_required_error_message = (
        "We need your understanding before we can help you")
    label = _(
        "Do you understand that if you are eligible, you might have to pay a "
        "fee in Yolo County? If you are low income, you may be eligible for "
        "a fee waiver.")
    agreement_text = _("Yes, I understand")
    display_label = str(
        "Understands that there may be a fee in Yolo County")


class ReasonsForApplying(MultipleChoiceField):
    context_key = "reasons_for_applying"
    label = _("Why are you applying to clear your record?")
    choices = REASON_FOR_APPLYING_CHOICES


class HowDidYouHear(CharField):
    context_key = "how_did_you_hear"
    label = _("How did you hear about this program or website?")
    display_label = "How they found out about this"


class AdditionalInformation(CharField):
    context_key = "additional_information"
    label = _("Is there anything else you would like us to know?")


class DeclarationLetterReviewActions(ChoiceField):
    context_key = 'submit_action'
    choices = DECLARATION_LETTER_REVIEW_CHOICES


class ApplicationReviewActions(ChoiceField):
    context_key = 'submit_action'
    choices = APPLICATION_REVIEW_CHOICES

###
# Identification Questions
###


class NameField(CharField):

    def get_display_value(self):
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


class Aliases(NameField):
    context_key = "aliases"
    label = _('Any other names that might be used on your record?')


number_validation_template = "Please enter a {field} between {min} and {max}"
month_validation_message = number_validation_template.format(
    field='month', min=1, max=12)
day_validation_message = number_validation_template.format(
    field='day', min=1, max=31)
year_validation_message = number_validation_template.format(
    field='year', min=1900, max=timezone.now().year)


class DisplayRawIfFalsyMixin:
    def get_display_value(self):
        return self.get_current_value() or self.raw_input_value


class Month(DisplayRawIfFalsyMixin, IntegerField):
    context_key = "month"
    label = _("Month")
    validators = [
        MinValueValidator(1, message=month_validation_message),
        MaxValueValidator(12, message=month_validation_message)
    ]

    def get_display_value(self):
        return self.get_current_value() or " "


class Day(DisplayRawIfFalsyMixin, IntegerField):
    context_key = "day"
    label = _("Day")
    validators = [
        MinValueValidator(1, message=day_validation_message),
        MaxValueValidator(31, message=day_validation_message)
    ]


class Year(DisplayRawIfFalsyMixin, IntegerField):
    context_key = "year"
    label = _("Year")
    validators = [
        MinValueValidator(1900, message=year_validation_message),
        MaxValueValidator(timezone.now().year, message=year_validation_message)
    ]


class DateOfBirthField(MultiValueField):
    context_key = "dob"
    label = _("What is your date of birth?")
    help_text = _("For example: 4/28/1986")
    is_required_error_message = _("The public defender may not be able to "
                                  "check your record without a full date "
                                  "of birth.")
    is_recommended_error_message = is_required_error_message
    subfields = [
        Month,
        Day,
        Year
    ]
    display_label = "Date of birth"

    def get_display_value(self):
        return "{month}/{day}/{year}".format(
            month=self.month.get_display_value(),
            day=self.day.get_display_value(),
            year=self.year.get_display_value()
        )


class SocialSecurityNumberField(CharField):
    context_key = "ssn"
    label = _('What is your Social Security Number? (if you have one)')
    help_text = _("The public defender's office will use this to "
                  "get your San Francisco record and find any "
                  "convictions that can be reduced or dismissed.")
    is_required_error_message = _("The public defender may not be able to "
                                  "check your record without a social "
                                  "security number.")
    is_recommended_error_message = is_required_error_message
    display_label = "SSN"


class LastFourOfSocial(CharField):
    context_key = "last_four"
    label = _(
        'What are the last 4 digits of your Social Security Number? '
        '(if you have one)')
    help_text = _(
        "This helps identify your case from people who have a "
        "similar name.")
    display_label = "SSN (Last 4)"


class DriverLicenseOrIDNumber(CharField):
    context_key = "driver_license_or_id"
    label = _("What is your Driver License or ID number? (if you have one)")
    help_text = _(
        "This helps identify your case from people who have a "
        "similar name.")
    display_label = "Driver License/ID"


class CaseNumber(CharField):
    context_key = "case_number"
    label = _("What is your case number, if you know it?")


class PFNNumber(CharField):
    context_key = "pfn_number"
    display_label = "PFN Number"
    label = _("What is your personal file number (PFN), if you know it?")
    help_text = _(
        "This is a number that is given to people who have been arrested in "
        "Santa Clara County that helps attorneys find your case. ")


###
# Contact Info Questions
###


class ContactPreferences(MultipleChoiceField):
    context_key = "contact_preferences"
    choices = CONTACT_PREFERENCE_CHOICES
    label = _(
        'How would you like Clear My Record to update you about your '
        'application?')
    help_text = _(
        'An attorney may need to send you official documents in the mail '
        'or call you to help with your case.')
    display_label = "Opted into Clear My Record updates via:"

    def get_display_value(self):
        return super().get_display_value(use_or=True)


class PreferredPronouns(ChoiceField):
    context_key = "preferred_pronouns"
    choices = GENDER_PRONOUN_CHOICES
    label = _('How would you like us to address you?')
    display_label = "Preferred pronouns"


class PhoneNumberField(PhoneField):
    context_key = "phone_number"
    help_text = _('For example, (555) 555-5555')
    label = _('What is your phone number?')
    autocomplete = "tel"


class AlternatePhoneNumberField(PhoneNumberField):
    context_key = "alternate_phone_number"
    label = _('What is another phone number we can reach you at?')


class FaxNumberField(PhoneNumberField):
    context_key = "fax_number"


class EmailField(CharField):
    context_key = "email"
    label = _('What is your email?')
    help_text = _('For example "yourname@example.com"')
    validators = [
        EmailValidator(_("Please enter a valid email")),
        mailgun_email_validator
    ]
    display_template_name = "formation/email_display.jinja"


class WebsiteField(CharField):
    context_key = "website"
    label = _("What is your website?")
    help_text = _('Like "example.com"')
    validators = [
        URLValidator(_("Please enter a valid URL")),
    ]
    display_template_name = "formation/url_display.jinja"


class Street(CharField):
    context_key = "street"
    autocomplete = "street-address"


class City(CharField):
    context_key = "city"
    label = _("City")
    autocomplete = "locality"


class State(CharField):
    context_key = "state"
    label = _("State")
    autocomplete = "region"


class Zip(CharField):
    context_key = "zip"
    label = _("Zip")
    autocomplete = "postal-code"


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

    def get_inline_display_value(self):
        return "{street}, {city}, {state} {zip}".format(
            **self.get_current_value())


class IsCaliforniaResident(YesNoField):
    context_key = "is_california_resident"
    label = _("Are you a current resident of California?")
    display_label = "California resident?"


class HowLongCaliforniaResident(CharField):
    context_key = "how_long_california_resident"
    label = _(
        "If you live in California, how long have you continuously lived "
        "here?")
    help_text = _("For example: 5 years")
    display_label = "How long?"


###
# Case status and screening
###

class USCitizen(YesNoField):
    context_key = "us_citizen"
    label = _("Are you a U.S. citizen?")
    help_text = _(
        "It is important for your attorney to know if you are a U.S citizen "
        "so they can find the best ways to help you. Your citizenship status "
        "will not be shared with any law enforcement agencies.")
    display_label = "Is a citizen"


class IsVeteran(YesNoField):
    context_key = "is_veteran"
    label = _("Are you a veteran?")


class IsStudent(YesNoField):
    context_key = "is_student"
    label = _("Are you a student?")


class BeingCharged(YesNoIDontKnowField):
    context_key = "being_charged"
    label = _("Are you currently being charged with a crime?")
    display_label = "Is currently being charged"
    flip_display_choice_order = True


class ServingSentence(YesNoIDontKnowField):
    context_key = "serving_sentence"
    label = _("Are you currently serving a sentence?")
    display_label = "Is serving a sentence"
    flip_display_choice_order = True


class OnProbationParole(YesNoIDontKnowField):
    context_key = "on_probation_parole"
    label = _("Are you on probation or parole (including MSR or PRCS)?")
    help_text = _(
        "MSR is mandatory supervised release and PRCS is post release "
        "community supervision")
    display_label = "Is on probation or parole"
    flip_display_choice_order = True


class WhereProbationParole(CharField):
    context_key = "where_probation_or_parole"
    label = _("If you are on probation or parole, what county is it in?")
    display_label = "Where"


class WhenProbationParole(CharField):
    context_key = "when_probation_or_parole"
    label = _("If you are on probation or parole, when does it end?")
    display_label = "Until"


class FinishedHalfProbation(YesNoIDontKnowField):
    context_key = "finished_half_probation"
    choices = YES_NO_IDK_CHOICES + ((NOT_APPLICABLE, _("Not on probation")),)
    label = _("If you're on probation, have you finished half of your "
              "probation time?")
    display_label = "Finished half probation"


class ReducedProbation(FinishedHalfProbation):
    context_key = "reduced_probation"
    label = _("If you're on probation, has the judge promised to reduce your "
              "probation time or end your probation early?")
    display_label = "Reduced probation"


class RAPOutsideSF(YesNoIDontKnowField):
    context_key = "rap_outside_sf"
    label = _(
        "Have you ever been arrested or convicted in any other counties?")
    display_label = "RAP in other counties"
    flip_display_choice_order = True


class WhenWhereOutsideSF(CharField):
    context_key = "when_where_outside_sf"
    label = _(
        "If you were arrested or convicted in other counties, which ones and "
        "when?")
    display_label = "Where/when"


class HasSuspendedLicense(ChoiceField):
    context_key = "has_suspended_license"
    label = _("Is your driver's license suspended?")
    display_label = "Has suspended license"
    flip_display_choice_order = True
    choices = YES_NO_IDK_CHOICES

    def get_display_choices(self):
        return YES_NO_IDK_CHOICES


class OwesCourtFees(YesNoIDontKnowField):
    context_key = "owes_court_fees"
    label = _("Do you owe any court fines or fees?")
    display_label = "Owes court fines/fees"
    flip_display_choice_order = True


class BeenToPrison(YesNoIDontKnowField):
    context_key = "has_been_to_prison"
    label = _("Have you been to prison?")
    flip_display_choice_order = True


###
# Financial Questions
###


class FinancialScreeningNote(FormNote):
    context_key = "financial_screening_note"
    content = _("Our partners use information about your income to "
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
    help_text = _("Include your spouse or legal partner's income. "
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
    label = _("Do you own a home or rental property?")


class MonthlyExpenses(WholeDollarField):
    context_key = "monthly_expenses"
    help_text = _("Your best estimate is okay.")
    label = _("How much do you spend each month on things like rent, "
              "groceries, utilities, medical expenses, or childcare expenses?")


class HowMuchSavings(WholeDollarField):
    context_key = "how_much_savings"
    help_text = _("Your best estimate is okay.")
    label = _("How much money do you have saved?")


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


class HowManyDependents(IntegerField):
    context_key = "dependents"
    label = ("How many people depend on your financial support?")


class IsMarried(YesNoField):
    context_key = "is_married"
    label = _("Are you married or in a legal domestic partnership?")


class HasChildren(YesNoField):
    context_key = "has_children"
    label = _("Do you have children?")


###
# Declaration Letter
###


class DeclarationLetterNote(FormNote):
    context_key = "declaration_letter_note"
    content = _("Create your letter to the judges in the counties you "
                "applied to. This is required to complete your application.")


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
    UnlistedCountyNote,
    UnlistedCounties,

    ContactPreferences,

    FirstName,
    MiddleName,
    LastName,
    Aliases,

    PreferredPronouns,

    PhoneNumberField,
    AlternatePhoneNumberField,
    EmailField,
    AddressField,
    IsCaliforniaResident,
    HowLongCaliforniaResident,
    DateOfBirthField,
    DriverLicenseOrIDNumber,
    LastFourOfSocial,
    SocialSecurityNumberField,
    CaseNumber,
    PFNNumber,

    USCitizen,
    IsVeteran,
    IsStudent,
    BeingCharged,
    ServingSentence,
    BeenToPrison,
    OnProbationParole,
    WhereProbationParole,
    WhenProbationParole,
    FinishedHalfProbation,
    ReducedProbation,
    RAPOutsideSF,
    WhenWhereOutsideSF,
    HasSuspendedLicense,
    OwesCourtFees,

    FinancialScreeningNote,
    CurrentlyEmployed,
    MonthlyIncome,
    IncomeSource,
    HowMuchSavings,
    OnPublicBenefits,
    MonthlyExpenses,
    OwnsHome,
    HouseholdSize,
    HasChildren,
    HowManyDependents,
    IsMarried,

    ReasonsForApplying,
    HowDidYouHear,
    AdditionalInformation,
    UnderstandsLimits,
    IdentityConfirmation,
    UnderstandsMaybeFee,
    ConsentToRepresent,
    ConsentNote,

    DeclarationLetterNote,
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
