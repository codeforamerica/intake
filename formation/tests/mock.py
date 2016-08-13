from formation import base
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDict
from formation.tests import rendered_samples as rendered
from faker import Factory as FakerFactory

sample_error_message = "not okay"

bad_email = "someone@nothing"
good_email = "someone@something.org"

fake = FakerFactory.create('en_US', includes=['intake.tests.mock_county_forms'])

RAW_FORM_DATA = MultiValueDict({
    'address.city': [''],
    'address.state': ['CA'],
    'address.street': [''],
    'address.zip': [''],
    'dob.day': [''],
    'dob.month': [''],
    'dob.year': [''],
    'drivers_license_number': [''],
    'email': [''],
    'first_name': [''],
    'how_did_you_hear': [''],
    'last_name': [''],
    'middle_name': [''],
    'monthly_expenses': [''],
    'monthly_income': [''],
    'phone_number': [''],
    'ssn': [''],
    'when_probation_or_parole': [''],
    'when_where_outside_sf': [''],
    'where_probation_or_parole': ['']
})

NEW_RAW_FORM_DATA = {
    'address.city': '',
    'address.state': 'CA',
    'address.street': '',
    'address.zip': '',
    'contact_preferences': ['prefers_email'],
    'dob.day': '',
    'dob.month': '',
    'dob.year': '',
    'email': 'foo@bar.com',
    'first_name': 'Foo',
    'how_did_you_hear': '',
    'last_name': 'Bar',
    'middle_name': '',
    'monthly_expenses': '',
    'monthly_income': '',
    'phone_number': '',
    'ssn': '',
    'when_probation_or_parole': '',
    'when_where_outside_sf': '',
    'where_probation_or_parole': '',
}


FILLED_SF_DATA = MultiValueDict({
 'address.city': ['New Anwarville'],
 'address.state': ['AZ'],
 'address.street': ['973 Migdalia Plain'],
 'address.zip': ['62145'],
 'being_charged': ['no'],
 'contact_preferences': ['prefers_sms'],
 'currently_employed': ['yes'],
 'dob.day': ['19'],
 'dob.month': ['3'],
 'dob.year': ['1999'],
 'email': ['anson16@gmail.com'],
 'first_name': ['Wess'],
 'how_did_you_hear': [''],
 'last_name': ['Kutch'],
 'middle_name': ['Gussie'],
 'monthly_expenses': ['803'],
 'monthly_income': ['6471'],
 'on_probation_parole': ['no'],
 'phone_number': ['671-928-8799'],
 'rap_outside_sf': ['no'],
 'serving_sentence': ['no'],
 'ssn': ['214259752'],
 'us_citizen': ['yes'],
 'when_probation_or_parole': [''],
 'when_where_outside_sf': [''],
 'where_probation_or_parole': ['']})

def post_data(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = [value] 
    return MultiValueDict(kwargs)

def form_answers(**kwargs):
    data = fake.sf_county_form_answers(**kwargs)
    return post_data(**data)

def simple_validator(value):
    raise ValidationError(sample_error_message)


class ContextValidator:
    def set_context(self, obj):
        self.form = obj

    def __call__(self, value):
        self.form.add_error(
            sample_error_message, "special")


context_validator = ContextValidator()


def list_validator(value):
    errors = [sample_error_message, sample_error_message]
    raise ValidationError(errors)


def dict_validator(value):
    raise ValidationError({
        "special": sample_error_message
        })


def dict_with_list_validator(value):
    raise ValidationError({
        "special": [sample_error_message, sample_error_message]
        })


def form_for_validator(validator, data=None):
    if not data:
        data = {}
    class Example(base.BindParseValidate):
        validators= [validator]
    return Example(data)


def mock_gettext(value=""):
    return value


def get_multivalue_examples(key, options):
    single = MultiValueDict({
        key: options[-1:] })
    multi = MultiValueDict({
        key: options })
    empty = MultiValueDict({
        key: [] })
    blank = MultiValueDict({
        key: [''] })
    missing = MultiValueDict({})
    return single, multi, empty, blank, missing

def get_dict_examples(key, valid, invalid):
    valid = {key: valid}
    invalid = {key: invalid}
    blank = {key: '' }
    missing = {}
    return valid, invalid, blank, missing


