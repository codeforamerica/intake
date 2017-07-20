from formation.combinable_base import CombinableFormSpec, FormSpecSelector
from formation.form_base import Form
from formation.display_form_base import DisplayForm
from formation import fields as F
from intake.constants import Counties, Organizations
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


class OtherCountyFormSpec(CombinableCountyFormSpec):
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


class SanFranciscoCountyFormSpec(CombinableCountyFormSpec):
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
        F.UnderstandsLimits,
        F.ConsentToRepresent,
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
    county = Counties.ALAMEDA
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
        F.DateOfBirthField,
        # F.LastFourOfSSN,
        F.USCitizen,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
        F.HasSuspendedLicense,
        F.OwesCourtFees,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
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


class AlamedaPublicDefenderFormSpec(CombinableOrganizationFormSpec):
    organization = Organizations.ALAMEDA_PUBDEF
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.MiddleName,
        F.LastName,
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.EmailField,
        F.AddressField,
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.OwnsHome,
        F.HouseholdSize,
        F.DateOfBirthField,
        F.USCitizen,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
        F.HowDidYouHear,
        F.AdditionalInformation,
    }
    required_fields = {
        F.FirstName,
        F.LastName,
        F.AddressField,
        F.DateOfBirthField,
        F.MonthlyIncome,
        F.OwnsHome,
        F.HouseholdSize,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
    }
    optional_fields = {
        F.AlternatePhoneNumberField,
        F.HowDidYouHear,
        F.AdditionalInformation,
    }


class MontereyCountyFormSpec(CombinableCountyFormSpec):
    county = Counties.MONTEREY
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
        F.USCitizen,
        F.IsVeteran,
        F.IsStudent,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.ServingSentence,
        F.BeingCharged,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
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
    county = Counties.SOLANO
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
        F.USCitizen,
        F.OnProbationParole,
        F.WhereProbationParole,
        F.WhenProbationParole,
        F.OwesCourtFees,
        F.ServingSentence,
        F.BeingCharged,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
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
    county = Counties.SAN_DIEGO
    fields = (SolanoCountyFormSpec.fields | {
        F.CaseNumber,
        F.IdentityConfirmation
    }) - {
        F.USCitizen,
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
    county = Counties.SAN_JOAQUIN
    validators = [
        gave_preferred_contact_methods
    ]


class FresnoCountyFormSpec(SolanoCountyFormSpec):
    county = Counties.FRESNO
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
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
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
    county = Counties.SANTA_CLARA
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
        F.USCitizen,
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
    county = Counties.SANTA_CRUZ
    fields = (SolanoCountyFormSpec.fields | {
        F.FinancialScreeningNote,
        F.MonthlyIncome,
        F.ReasonsForApplying
    }) - {
        F.OwesCourtFees,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF
    }
    required_fields = SolanoCountyFormSpec.required_fields - {
        F.OwesCourtFees,
    }


class SonomaCountyFormSpec(SolanoCountyFormSpec):
    county = Counties.SONOMA
    validators = [
        gave_preferred_contact_methods
    ]


class TulareCountyFormSpec(SolanoCountyFormSpec):
    county = Counties.TULARE
    validators = [
        gave_preferred_contact_methods
    ]


class VenturaCountyFormSpec(CombinableCountyFormSpec):
    county = Counties.VENTURA
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
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
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
    county = Counties.SANTA_BARBARA
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
    county = Counties.YOLO
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
        F.USCitizen
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
    county = Counties.STANISLAUS
    fields = FresnoCountyFormSpec.fields - {
        F.DriverLicenseOrIDNumber,
        F.LastFourOfSocial,
        F.CaseNumber,
        F.USCitizen,
        F.MonthlyIncome,
        F.IncomeSource,
        F.HowMuchSavings,
        F.HowManyDependents
    }
    required_fields = (FresnoCountyFormSpec.required_fields)


class EBCLCIntakeFormSpec(CombinableOrganizationFormSpec):
    organization = Organizations.EBCLC
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
        F.DateOfBirthField,
        # F.LastFourOfSocial,
        F.USCitizen,
        F.OnProbationParole,
        F.FinishedHalfProbation,
        F.ReducedProbation,
        F.ServingSentence,
        F.BeingCharged,
        F.RAPOutsideSF,
        F.WhenWhereOutsideSF,
        F.HasSuspendedLicense,
        F.OwesCourtFees,
        F.HowDidYouHear,
        F.AdditionalInformation,
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
    }
    optional_fields = {
        F.AlternatePhoneNumberField,
        F.HowDidYouHear,
        F.AdditionalInformation,
    }


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


class DeclarationLetterReviewForm(Form):
    fields = [F.DeclarationLetterReviewActions]
    required_fields = [F.DeclarationLetterReviewActions]


class SelectCountyForm(Form):
    fields = [
        F.Counties,
        F.AffirmCountySelection
    ]
    required_fields = [
        F.Counties,
        F.AffirmCountySelection]


INPUT_FORM_SPECS = [
    OtherCountyFormSpec(),
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
    StanislausCountyFormSpec()
]

DISPLAY_FORM_SPECS = INPUT_FORM_SPECS + [
    SupplementaryDisplayForm(),
]

ORG_FORM_SPECS = [
    AlamedaPublicDefenderFormSpec(),
    EBCLCIntakeFormSpec(),
]

display_form_selector = FormSpecSelector(DISPLAY_FORM_SPECS, DisplayForm)
county_form_selector = FormSpecSelector(INPUT_FORM_SPECS, Form)
organization_form_selector = FormSpecSelector(ORG_FORM_SPECS, Form)
