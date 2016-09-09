import inspect
from formation.tests.utils import PatchTranslationTestCase, django_only
from formation.tests import mock

from formation.forms import county_form_selector
from formation import fields as F
from formation.field_base import Field
from formation.forms import SelectCountyForm
from formation.form_base import Form
from intake.constants import Counties
from formation import validators


class TestForm(PatchTranslationTestCase):

    def get_sf_form(self, *args):
        form_class = county_form_selector.get_combined_form_class(
            counties=[Counties.SAN_FRANCISCO])
        return form_class(*args)

    def test_does_not_alter_class_attributes_after_instantiation(self):
            # make sure we have a class
            form = SelectCountyForm({})
            self.assertFalse(form.is_valid())
            form = SelectCountyForm({})
            self.assertEqual(SelectCountyForm.required_fields[0], F.Counties)

    def test_can_be_instantiated_with_multivalue_dict(self):
        form = self.get_sf_form(mock.RAW_FORM_DATA)
        self.assertFalse(form.is_valid())

    def test_application_form_with_raw_empty_post_data(self):
        # Application form should not have trouble reading raw post data from
        # a Django request. But the form should not be valid
        form = self.get_sf_form(mock.RAW_FORM_DATA)
        self.assertTrue(not form.is_valid())
        keys = form.errors.keys()
        self.assertTrue('first_name' in keys)
        self.assertTrue('last_name' in keys)
        self.assertEqual(len(keys), 2)

    def test_application_form_with_mock_answers(self):
        fake_answers = mock.form_answers()
        form = self.get_sf_form(fake_answers)
        self.assertTrue(form.is_valid())

    def test_empty_value_is_as_expected(self):
        expected_empty_value = {
            'address': {
                'city': '',
                'state': '',
                'street': '',
                'zip': ''
            },
            'contact_preferences': [],
            'currently_employed': '',
            'dob': {
                'day': '',
                'month': '',
                'year': ''
            },
            'email': '',
            'first_name': '',
            'how_did_you_hear': '',
            'last_name': '',
            'middle_name': '',
            'monthly_expenses': '',
            'monthly_income': None,
            'on_probation_parole': '',
            'phone_number': '',
            'rap_outside_sf': '',
            'serving_sentence': '',
            'being_charged': '',
            'ssn': '',
            'us_citizen': '',
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'additional_information': '',
        }
        form = self.get_sf_form()
        self.assertDictEqual(form.empty_value, expected_empty_value)
        form = self.get_sf_form({})
        self.assertDictEqual(form.empty_value, expected_empty_value)

    def test_can_be_instantiated_with_preparsed_data(self):
        preparsed = {
            'address': {
                'city': 'East Moemouth',
                'state': 'HI',
                'street': '220 Lynch Walk',
                'zip': '46885'},
            'contact_preferences': [
                'prefers_voicemail',
                'prefers_sms',
                'prefers_email'],
            'currently_employed': 'yes',
            'dob': {'day': '2', 'month': '12', 'year': '1998'},
            'email': 'shaun68@yahoo.com',
            'first_name': 'Erwin',
            'how_did_you_hear': '',
            'last_name': 'Johnson',
            'middle_name': 'Horace',
            'monthly_expenses': '1301',
            'monthly_income': 2465,
            'on_probation_parole': 'yes',
            'phone_number': '590-133-5279',
            'rap_outside_sf': 'no',
            'serving_sentence': 'yes',
            'being_charged': 'no',
            'ssn': '479928924',
            'us_citizen': 'yes',
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'additional_information': 'foo bar',
        }
        form = self.get_sf_form(preparsed)
        self.assertTrue(form.is_valid())
        self.assertDictEqual(form.cleaned_data, preparsed)

    def test_can_get_fields_through_context_key_as_attr(self):
        form = self.get_sf_form()
        self.assertTrue(isinstance(form.address, Field))
        self.assertTrue(isinstance(form.contact_preferences, Field))
        self.assertTrue(isinstance(form.dob, Field))
        self.assertTrue(isinstance(form.email, Field))
        self.assertTrue(isinstance(form.phone_number, Field))
        self.assertTrue(isinstance(form.first_name, Field))

    def test_preferred_contact_methods(self):
        contact_preferences = [
            "prefers_email",
            "prefers_sms",
            "prefers_snailmail",
            "prefers_voicemail"
        ]
        form = self.get_sf_form(dict(contact_preferences=contact_preferences))
        error_messages = [
            validators.gave_preferred_contact_methods.message(k)
            for k in contact_preferences
        ]
        self.assertFalse(form.is_valid())
        errors = form.errors
        self.assertIn(validators.gave_preferred_contact_methods.message(
            'prefers_sms'), errors['phone_number'])
        self.assertIn(validators.gave_preferred_contact_methods.message(
            'prefers_voicemail'), errors['phone_number'])
        self.assertIn(validators.gave_preferred_contact_methods.message(
            'prefers_email'), errors['email'])
        self.assertIn(validators.gave_preferred_contact_methods.message(
            'prefers_snailmail'), errors['address'])
        # case: only required errors, no contact info erros
        form = self.get_sf_form(mock.post_data(**{
            'contact_preferences': contact_preferences,
            'address.street': '111 Main St.',
            'address.city': 'Oakland',
            'address.state': 'CA',
            'address.zip': '94609',
            'phone_number': '415-333-4444',
            'email': 'someone@gmail.com'
        }))
        self.assertFalse(form.is_valid())
        self.assertFalse('phone_number' in form.errors)
        self.assertFalse('email' in form.errors)
        self.assertFalse('address' in form.errors)

    @django_only
    def test_form_display(self):
        fake_answers = mock.FILLED_SF_DATA
        form = self.get_sf_form(fake_answers)
        self.assertTrue(form.is_valid())
        self.assertTrue(hasattr(form.display(), '__html__'))
