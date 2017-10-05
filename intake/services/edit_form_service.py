from formation import fields as F
from formation.field_types import MultiValueField
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
    # get all orgs for submissison
    all_county_slugs = submission.organizations.values_list(
        'county__slug', flat=True)
    # get combined form spec for all orgs
    all_county_form_spec = county_form_selector.get_combined_form_spec(
        counties=all_county_slugs)
    county_field_set = all_county_form_spec.fields

    if not user.is_staff:
        user_county_slug = user.profile.organization.county.slug
        user_county_spec = county_form_selector.get_combined_form_spec(
            counties=[user_county_slug])
        county_field_set = user_county_spec.fields

    form_field_set = county_field_set & EDITABLE_FIELDS
    form_fields = sorted(list(form_field_set), key=get_field_index)
    # get union of required fields from all form specs
    # this, intersected with form_fields, is the set of required fields for
    # our form
    required_fields = list(
        all_county_form_spec.required_fields & form_field_set)
    parent_classes = (Form,)
    class_attributes = dict(
        fields=form_fields,
        required_fields=required_fields,
        validators=list(all_county_form_spec.validators))
    return type('CombinedEditForm', parent_classes, class_attributes)


def has_errors_on_existing_data_only(form, submission):
    for field_key in form.errors:
        if form.fields[field_key].get_current_value() != \
                submission.answers[field_key]:
            return False
    return True


def remove_errors_for_existing_data(form, submission):
    errors = form.errors.copy()
    for field_key in errors:
        if form.fields[field_key].get_current_value() == \
                submission.answers[field_key]:
            del form.errors[field_key]
            field = form.fields[field_key]
            field.errors = {}
            if isinstance(field, MultiValueField):
                for subfield in field.subfields:
                    subfield.errors = {}
