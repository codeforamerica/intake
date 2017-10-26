from formation.combinable_base import CombinableFormSpec, FormSpecSelector
from formation.form_base import Form
from formation.display_form_base import DisplayForm
from formation import fields as F
from formation.validators import (
    gave_preferred_contact_methods, at_least_email_or_phone
)


class CombinableCountyFormSpec(CombinableFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        counties = kwargs.get('counties', [])
        return self.county in counties


class CombinableOrganizationFormSpec(CombinableFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        organizations = kwargs.get('organizations', [])
        return self.organization in organizations


class SupplementaryDisplayForm(CombinableCountyFormSpec):

    def is_correct_spec(self, *args, **kwargs):
        return True

    fields = {
        F.DateReceived,
        F.Counties,
    }


class NotListedFormSpec(CombinableCountyFormSpec):
    """This could be used by Code for America to send applicants
    information on clean slate services in other counties or states.
    """
    county = 'not_listed'
    fields = {
        F.UnlistedCountyNote,
        F.UnlistedCounties,
        F.FirstName,
        F.LastName,
        F.PhoneNumberField,
        F.EmailField,
        F.HowDidYouHear,
        F.AdditionalInformation,
    }
    required_fields = {
        F.UnlistedCounties,
        F.FirstName
    }
    optional_fields = {
        F.HowDidYouHear,
        F.AdditionalInformation
    }
    validators = [
        at_least_email_or_phone
    ]


class SanFranciscoCountyFormSpec(CombinableCountyFormSpec):
    county = 'sanfrancisco'
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
        F.CitizenshipStatus,
        F.ServingSentence,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.BeingCharged,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.MonthlyExpenses,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    recommended_fields = {
        F.AddressField,
        F.DateOfBirthField,
        F.SocialSecurityNumberField,
    }
    optional_fields = {
        F.HowDidYouHear,
        F.MiddleName,
        F.AdditionalInformation,
    }
    validators = [
        gave_preferred_contact_methods
    ]


class ContraCostaFormSpec(CombinableCountyFormSpec):
    county = 'contracosta'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.DateOfBirthField,
        F.CitizenshipStatus,
        F.ServingSentence,
        F.OnProbationParole,
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.HowDidYouHear,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
        F.AdditionalInformation
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.AddressField,
        F.CitizenshipStatus,
        F.CurrentlyEmployed,
        F.DateOfBirthField,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.ServingSentence,
        F.OnProbationParole,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    optional_fields = {
        F.HowDidYouHear,
        F.AdditionalInformation
    }
    validators = [
        gave_preferred_contact_methods
    ]


class AlamedaCountyFormSpec(CombinableCountyFormSpec):
    county = 'alameda'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PreferredPronouns,
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.OnPublicBenefits,
        F.OwnsHome,
        F.HouseholdSize,
        F.ReasonsForApplying,
        F.DateOfBirthField,
        F.CitizenshipStatus,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
        F.HasSuspendedLicense,
        F.OwesCourtFees,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
        F.HasBeenDeniedHousingOrEmployment,
        F.WhoWhenDeniedHousingOrEmployment,
        F.IsRegisteredUnderPc290,
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
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    optional_fields = {
        F.AlternatePhoneNumberField,
        F.HowDidYouHear,
        F.AdditionalInformation,
    }
    validators = [
        gave_preferred_contact_methods
    ]


class MontereyCountyFormSpec(CombinableCountyFormSpec):
    county = 'monterey'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.OnPublicBenefits,
        F.HouseholdSize,
        F.DateOfBirthField,
        F.CitizenshipStatus,
        F.IsVeteran,
        F.IsStudent,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.ServingSentence,
        F.BeingCharged,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.AddressField,
        F.DateOfBirthField,
        F.MonthlyIncome,
        F.OnPublicBenefits,
        F.HouseholdSize,
        F.OnProbationParole,
        F.ServingSentence,
        F.BeingCharged,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    optional_fields = {
        F.HowDidYouHear,
        F.AdditionalInformation,
    }
    validators = [
        gave_preferred_contact_methods
    ]


class SolanoCountyFormSpec(CombinableCountyFormSpec):
    county = 'solano'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.DateOfBirthField,
        F.CitizenshipStatus,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.OwesCourtFees,
        F.ServingSentence,
        F.BeingCharged,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.DateOfBirthField,
        F.OnProbationParole,
        F.OwesCourtFees,
        F.ServingSentence,
        F.BeingCharged,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    optional_fields = {
        F.MiddleName,
        F.AlternatePhoneNumberField,
        F.HowDidYouHear,
        F.AdditionalInformation
    }
    validators = [
        gave_preferred_contact_methods,
        at_least_email_or_phone
    ]


class SanDiegoCountyFormSpec(SolanoCountyFormSpec):
    county = 'san_diego'
    fields = (SolanoCountyFormSpec.fields | {
        F.CaseNumber,
        F.IdentityConfirmation
    }) - {
        F.CitizenshipStatus,
    }
    required_fields = SolanoCountyFormSpec.required_fields | {
        F.IdentityConfirmation
    }
    optional_fields = SolanoCountyFormSpec.optional_fields | {
        F.CaseNumber
    }
    validators = [
        gave_preferred_contact_methods,
        at_least_email_or_phone
    ]


class SanJoaquinCountyFormSpec(SolanoCountyFormSpec):
    county = 'san_joaquin'
    validators = [
        gave_preferred_contact_methods
    ]


class FresnoCountyFormSpec(SolanoCountyFormSpec):
    county = 'fresno'
    fields = (SolanoCountyFormSpec.fields | {
        F.Aliases,
        F.CaseNumber,
        F.ReasonsForApplying,
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.HowManyDependents,
        F.LastFourOfSocial,
        F.DriverLicenseOrIDNumber,
    }) - {
        F.OwesCourtFees,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
    }
    optional_fields = SolanoCountyFormSpec.optional_fields | {
        F.Aliases,
    }
    required_fields = SolanoCountyFormSpec.required_fields - {
        F.OwesCourtFees,
    }
    validators = [
        gave_preferred_contact_methods
    ]


class SantaClaraCountyFormSpec(SolanoCountyFormSpec):
    county = 'santa_clara'
    fields = (SolanoCountyFormSpec.fields | {
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.OnPublicBenefits,
        F.HouseholdSize,
        F.IsMarried,
        F.HasChildren,
        F.IsVeteran,
        F.ReducedProbation,
        F.ReasonsForApplying,
        F.PFNNumber,
        F.PreferredPronouns,
    }) - {
        F.CitizenshipStatus,
    }
    required_fields = (SolanoCountyFormSpec.required_fields | {
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.OnPublicBenefits,
        F.HouseholdSize,
    }) - {F.PhoneNumberField}
    validators = [
        gave_preferred_contact_methods
    ]


class SantaCruzCountyFormSpec(SolanoCountyFormSpec):
    county = 'santa_cruz'
    fields = (SolanoCountyFormSpec.fields | {
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.ReasonsForApplying
    }) - {
        F.OwesCourtFees,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties
    }
    required_fields = SolanoCountyFormSpec.required_fields - {
        F.OwesCourtFees,
    }


class SonomaCountyFormSpec(SolanoCountyFormSpec):
    county = 'sonoma'
    validators = [
        gave_preferred_contact_methods
    ]


class TulareCountyFormSpec(SolanoCountyFormSpec):
    county = 'tulare'
    validators = [
        gave_preferred_contact_methods
    ]


class VenturaCountyFormSpec(CombinableCountyFormSpec):
    county = 'ventura'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.IsCaliforniaResident,
        F.HowLongCaliforniaResident,
        F.OwnsHome,
        F.FinancialScreeningNote,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.OnPublicBenefits,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HowManyDependents,
        F.IsVeteran,
        F.DateOfBirthField,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.OwesCourtFees,
        F.ServingSentence,
        F.BeingCharged,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.CaseNumber,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    required_fields = {
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HowManyDependents,
        F.OnPublicBenefits,
        F.HouseholdSize,
        F.DateOfBirthField,
        F.OnProbationParole,
        F.OwesCourtFees,
        F.ServingSentence,
        F.BeingCharged,
        F.UnderstandsLimits,
        F.ConsentToRepresent,
    }
    validators = [
        gave_preferred_contact_methods,
        at_least_email_or_phone
    ]


class SantaBarbaraCountyFormSpec(VenturaCountyFormSpec):
    county = 'santa_barbara'
    fields = (VenturaCountyFormSpec.fields | {
        F.Aliases,
        F.ReasonsForApplying,
        F.IsMarried,
        F.HowMuchSavings,
        F.DriverLicenseOrIDNumber,
        F.WhenProbationParole}) - {
        F.IsCaliforniaResident,
        F.HowLongCaliforniaResident,
        F.IsVeteran,
    }
    required_fields = (
        VenturaCountyFormSpec.required_fields | {F.HowMuchSavings})


class YoloCountyFormSpec(SonomaCountyFormSpec):
    county = 'yolo'
    fields = (SonomaCountyFormSpec.fields | {
        F.Aliases,
        F.CaseNumber,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.OnPublicBenefits,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HasChildren,
        F.HowManyDependents,
        F.IsMarried,
        F.UnderstandsMaybeFee
    }) - {
        F.AlternatePhoneNumberField,
        F.OwesCourtFees,
        F.ServingSentence,
        F.CitizenshipStatus
    }
    required_fields = (SonomaCountyFormSpec.required_fields | {
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HowManyDependents,
        F.IsMarried,
        F.ReasonsForApplying,
        F.UnderstandsMaybeFee
        }) - {
        F.OwesCourtFees,
    }


class StanislausCountyFormSpec(FresnoCountyFormSpec):
    county = 'stanislaus'
    fields = (FresnoCountyFormSpec.fields | {
        F.BeenToPrison,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.OwesCourtFees,
    }) - {
        F.DriverLicenseOrIDNumber,
        F.LastFourOfSocial,
        F.CaseNumber,
        F.CitizenshipStatus,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.HowManyDependents
    }
    required_fields = FresnoCountyFormSpec.required_fields


class MarinCountyFormSpec(CombinableCountyFormSpec):
    county = 'marin'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.Aliases,
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.DateOfBirthField,
        F.DriverLicenseOrIDNumber,
        F.SocialSecurityNumberField,
        F.CaseNumber,
        F.BeingCharged,
        F.ServingSentence,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.OtherCountyArrestsOrConvictions,
        F.WhenWhereOtherCounties,
        F.OwesCourtFees,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.OtherIncome,
        F.OnPublicBenefits,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HasChildren,
        F.HowManyDependents,
        F.IsMarried,
        F.ReasonsForApplying,
        F.HowDidYouHear,
        F.AdditionalInformation,
        F.UnderstandsLimits,
        F.ConsentToRepresent
    }
    required_fields = {
        F.ContactPreferences,
        F.FirstName,
        F.LastName,
        F.PhoneNumberField,
        F.AddressField,
        F.DateOfBirthField,
        F.BeingCharged,
        F.ServingSentence,
        F.OnProbationParole,
        F.OwesCourtFees,
        F.CurrentlyEmployed,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.OnPublicBenefits,
        F.MonthlyExpenses,
        F.OwnsHome,
        F.HasChildren,
        F.HowManyDependents,
        F.IsMarried,
        F.UnderstandsLimits,
        F.ConsentToRepresent
    }
    validators = [
        gave_preferred_contact_methods
    ]


class DeclarationLetterFormSpec(CombinableFormSpec):
    fields = {
        F.DeclarationLetterNote,
        F.DeclarationLetterIntro,
        F.DeclarationLetterLifeChanges,
        F.DeclarationLetterActivities,
        F.DeclarationLetterGoals,
        F.DeclarationLetterWhy,
    }
    required_fields = {
        F.DeclarationLetterIntro,
        F.DeclarationLetterLifeChanges,
        F.DeclarationLetterActivities,
        F.DeclarationLetterGoals,
        F.DeclarationLetterWhy,
    }


class DeclarationLetterDisplay(DisplayForm):
    display_template_name = "forms/declaration_letter_display.jinja"
    fields = [
        F.DateReceived,
        F.DeclarationLetterIntro,
        F.DeclarationLetterLifeChanges,
        F.DeclarationLetterActivities,
        F.DeclarationLetterGoals,
        F.DeclarationLetterWhy,
        F.FirstName,
        F.MiddleName,
        F.LastName,
    ]


class ApplicationReviewForm(Form):
    fields = [F.ApplicationReviewActions]
    required_fields = [F.ApplicationReviewActions]


class DeclarationLetterReviewForm(Form):
    fields = [F.DeclarationLetterReviewActions]
    required_fields = [F.DeclarationLetterReviewActions]


class SelectCountyForm(Form):
    fields = [F.Counties]
    required_fields = [F.Counties]


INPUT_FORM_SPECS = [
    NotListedFormSpec(),
    SanFranciscoCountyFormSpec(),
    ContraCostaFormSpec(),
    AlamedaCountyFormSpec(),
    MontereyCountyFormSpec(),
    SolanoCountyFormSpec(),
    SanDiegoCountyFormSpec(),
    SanJoaquinCountyFormSpec(),
    SantaClaraCountyFormSpec(),
    SantaCruzCountyFormSpec(),
    FresnoCountyFormSpec(),
    SonomaCountyFormSpec(),
    TulareCountyFormSpec(),
    VenturaCountyFormSpec(),
    SantaBarbaraCountyFormSpec(),
    YoloCountyFormSpec(),
    StanislausCountyFormSpec(),
    MarinCountyFormSpec()
]

DISPLAY_FORM_SPECS = INPUT_FORM_SPECS + [
    SupplementaryDisplayForm(),
]

display_form_selector = FormSpecSelector(DISPLAY_FORM_SPECS, DisplayForm)
county_display_form_selector = FormSpecSelector(INPUT_FORM_SPECS, DisplayForm)
county_form_selector = FormSpecSelector(INPUT_FORM_SPECS, Form)


def print_all_fields_for_county(county_slug):
    form_class = county_form_selector.get_combined_form_class(
        counties=[county_slug])
    for field in form_class.fields:
        output = '\t{}'.format(field.context_key)
        if field in form_class.required_fields:
            output += ' (R)'
        print(output)


def print_all_forms():
    from user_accounts.models import Organization
    for org in Organization.objects.all():
        print('\n{}'.format(org.name))
        print_all_fields_for_county(org.county.slug)
