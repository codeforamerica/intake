from formation.combinable_base import CombinableFormSpec, FormSpecSelector
from formation.form_base import Form
from formation import fields as F
from intake.constants import Counties
from formation.validators import gave_preferred_contact_methods

class CombinableCountyFormSpec(CombinableFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        counties = kwargs.get('counties', [])
        return self.county in counties



class OtherCountyForm(CombinableCountyFormSpec):
    """This is used by Code for America to send applicants
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
        F.CaseNumber,
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


class SelectCountyForm(Form):
    fields = [F.Counties]
    required_fields = [F.Counties]


county_form_selector = FormSpecSelector([
    OtherCountyForm(),
    SanFranciscoCountyForm(),
    ContraCostaForm()
])