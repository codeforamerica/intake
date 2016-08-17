from formation.combinable_base import CombinableFormSpec, FormSpecSelector
from formation.form_base import Form
from formation.display_form_base import DisplayForm
from formation import fields as F
from intake.constants import Counties
from formation.validators import gave_preferred_contact_methods


class CombinableCountyFormSpec(CombinableFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        counties = kwargs.get('counties', [])
        return self.county in counties


class SupplementaryDisplayForm(CombinableCountyFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        return True

    fields = {
        F.DateReceived,
        F.Counties,       
    }


class OtherCountyForm(CombinableCountyFormSpec):
    """This could be used by Code for America to send applicants
    information on clean slate services in other counties or states.
    """
    county = Counties.OTHER
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.HowDidYouHear,
    }
    required_fields = {
        F.ContactPreferences,
        F.FirstName
    }
    optional_fields = {
        F.HowDidYouHear
    }
    validators = [
        gave_preferred_contact_methods
    ]



class SanFranciscoCountyForm(CombinableCountyFormSpec):
    county = Counties.SAN_FRANCISCO
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.DateOfBirthField,
        F.SocialSecurityNumberField,
        F.USCitizen,
        F.ServingSentence,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.BeingCharged,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.MonthlyExpenses,
        F.HowDidYouHear
    }
    required_fields = {
        F.FirstName,
        F.LastName
    }
    recommended_fields = {
        F.AddressField,
        F.DateOfBirthField,
        F.SocialSecurityNumberField,
    }
    optional_fields = {
        F.HowDidYouHear,
        F.MiddleName
    }
    validators = [
        gave_preferred_contact_methods
    ]


class ContraCostaForm(CombinableCountyFormSpec):
    county = Counties.CONTRA_COSTA
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.DateOfBirthField,
        F.USCitizen,
        F.ServingSentence,
        F.OnProbationParole,
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.HowDidYouHear,
        F.AdditionalInformation
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.AddressField,
        F.USCitizen,
        F.CurrentlyEmployed,
        F.DateOfBirthField,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.ServingSentence,
        F.OnProbationParole,
    }
    optional_fields = {
        F.HowDidYouHear,
        F.AdditionalInformation
    }
    validators = [
        gave_preferred_contact_methods
    ]

class AlamedaCountyForm(CombinableCountyFormSpec):
    county = Counties.ALAMEDA
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PreferredPronouns,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.OnPublicBenefits,
        F.OwnsHome,
        F.HouseholdSize,
        F.DateOfBirthField,
        #F.LastFourOfSSN,
        F.USCitizen,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ServingSentence,
        F.BeingCharged,
        #F.HasExternalRAP,
        #F.ExternalRAPWhereWhen,
        F.HowDidYouHear,
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.AddressField,
        F.DateOfBirthField,
        F.MonthlyIncome,
        F.OnPublicBenefits,
        F.OwnsHome,
        F.HouseholdSize,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ServingSentence,
        F.BeingCharged,
    }
    optional_fields = {
        F.HowDidYouHear,
    }


# class DeclarationLetterForm(CombinableFormSpec):
#     fields = {
#         # F.ContactPreferences,
#         # F.FirstName,
#         # F.MiddleName,
#         # F.LastName,
#         # #F.PreferredPronouns,
#         # F.PhoneNumberField,
#         # F.EmailField,
#         # F.AddressField,
#         # F.FinancialScreeningNote,
#         # F.MonthlyIncome,
#         # #F.OnPublicBenefits,
#         # #F.HomeOwner,
#         # #F.HouseholdSize,
#         # F.DateOfBirthField,
#         # #F.LastFourOfSSN,
#         # F.USCitizen,
#         # F.OnProbationParole,
#         # #F.FinishedHalfProbation,
#         # F.ServingSentence,
#         # F.BeingCharged,
#         # #F.HasExternalRAP,
#         # #F.ExternalRAPWhereWhen
#     }


class SelectCountyForm(Form):
    fields = [F.Counties]
    required_fields = [F.Counties]


INPUT_FORM_SPECS = [
    OtherCountyForm(),
    SanFranciscoCountyForm(),
    ContraCostaForm(),
    AlamedaCountyForm(),
]
DISPLAY_FORM_SPECS = INPUT_FORM_SPECS + [
    SupplementaryDisplayForm(),
]

county_form_selector = FormSpecSelector(INPUT_FORM_SPECS, Form)
display_form_selector = FormSpecSelector(DISPLAY_FORM_SPECS, DisplayForm)
