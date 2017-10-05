from formation import fields as F
from formation.fields import get_field_index
from formation.form_base import Form
from formation.forms import county_form_selector

EDITABLE_FIELDS = {
    F.ContactPreferences,
    F.FirstName,
    F.MiddleName,
    F.LastName,
    F.Aliases,
    F.PhoneNumberField,
    F.AlternatePhoneNumberField,
    F.AddressField,
    F.DriverLicenseOrIDNumber,
    F.EmailField,
    F.DateOfBirthField,
    F.SocialSecurityNumberField,
    F.CaseNumber
}

def get_edit_form_class_for_user_and_submission(user, submission):
    user_county_slug = user.profile.organization.county.slug
    user_county_spec = county_form_selector.get_combined_form_spec(
        counties=[user_county_slug])

    field_set = user_county_spec.fields & EDITABLE_FIELDS
    fields = sorted(list(field_set), key=get_field_index)

    # get all orgs for submissison
    # get form spec for each org
    # get union of required fields from all form specs
    # this, intersected with form_fields, is the set of required fields for our form

    # validators: always do "gave_preferred_contact_methods"
    # If any org requires at least email or phone, do that too

    # generate a form class using form_fields and required_form_fields and validators
    return type(
        'CombinedForm',
        (Form,),
        {
            'fields': fields,
            'required_fields': [],
            'validators': []
        }
    )
