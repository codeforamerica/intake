from intake.forms.form_base import CombinableForm
from intake.constants import Counties

from intake.forms import fields as F


class OtherCountyForm(CombinableForm):
    """This is used by Code for America to send applicants
    information on clean slate services in other counties or states.
    """
    counties = {Counties.OTHER}
    fields = {
        F.contact_preferences,
        F.first_name,
        F.phone_number,
        F.email,
        F.address,
        F.how_did_you_hear
    }
    required_fields = {
        F.contact_preferences,
        F.first_name,
    }


class SanFranciscoCountyForm(CombinableForm):
    counties = {Counties.SAN_FRANCISCO}
    fields = {
        F.contact_preferences,
        F.first_name,
        F.middle_name,
        F.last_name,
        F.phone_number,
        F.email,
        F.address,
        F.dob,
        F.ssn,
        F.us_citizen,
        F.serving_sentence,
        F.on_probation_parole,
        F.where_probation_or_parole,
        F.when_probation_or_parole,
        F.rap_outside_sf,
        F.when_where_outside_sf,
        F.financial_screening_note,
        F.currently_employed,
        F.monthly_income,
        F.monthly_expenses,
        F.how_did_you_hear,
    }
    required_fields = {
        F.first_name,
        F.last_name,
    }
    recommended_fields = {
        F.address,
        F.dob,
        F.ssn
    }


class ContraCostaForm(CombinableForm):
    """Based on
    https://ca-contracostacounty2.civicplus.com/FormCenter/Public-Defender-7/Prop-47-Contact-Form-144/
    """
    counties = {Counties.CONTRA_COSTA}
    fields = {
        F.contact_preferences,
        F.first_name,
        F.middle_name,
        F.last_name,
        F.phone_number,
        F.email,
        F.address,
        F.dob,
        F.us_citizen,
        F.serving_sentence,
        F.on_probation_parole,
        F.financial_screening_note,
        F.currently_employed,
        F.monthly_income,
        F.income_source,
        F.monthly_expenses,
        F.case_number,
        F.how_did_you_hear,
        F.additional_information
    }
    required_fields = {
        F.first_name,
        F.last_name,
        F.address,
        F.us_citizen,
        F.currently_employed,
        F.dob,
        F.monthly_income,
        F.income_source,
        F.monthly_expenses,
        F.serving_sentence,
        F.on_probation_parole,
    }

ALL_FORMS = [
    OtherCountyForm,
    SanFranciscoCountyForm,
    ContraCostaForm
]

def get_form_for_counties(counties):
    combined_form = None
    for county in counties:
        for form in ALL_FORMS:
            if county in form.counties:
                if combined_form is None:
                    combined_form = form
                else:
                    combined_form |= form
    return combined_form
   