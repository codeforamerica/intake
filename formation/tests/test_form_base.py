from unittest.mock import Mock
from django.test import TestCase
from formation.tests import mock

from formation.forms import county_form_selector
from formation import fields as F
from formation.field_types import IntegerField
from formation.field_base import Field
from formation.form_base import Form
from formation import validators


class ExampleForm(Form):
    fields = [F.FirstName]
    required_fields = [F.FirstName]


class TestForm(TestCase):

    def get_sf_form(self, *args):
        form_class = county_form_selector.get_combined_form_class(
            counties=['sanfrancisco'])
        return form_class(*args)

    def test_does_not_alter_class_attributes_after_instantiation(self):
        # make sure we have a class
        form = ExampleForm({})
        self.assertFalse(form.is_valid())
        form = ExampleForm({})
        self.assertEqual(ExampleForm.required_fields[0], F.FirstName)

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
        self.assertTrue('understands_limits' in keys)
        self.assertTrue('consent_to_represent' in keys)
        self.assertEqual(len(keys), 4)

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
                'day': None,
                'month': None,
                'year': None
            },
            'email': '',
            'first_name': '',
            'how_did_you_hear': '',
            'last_name': '',
            'middle_name': '',
            'monthly_expenses': None,
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
            'consent_to_represent': '',
            'understands_limits': '',
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
                'prefers_sms',
                'prefers_email'],
            'currently_employed': 'yes',
            'dob': {'day': 2, 'month': 12, 'year': 1998},
            'email': 'cmrtestuser@gmail.com',
            'first_name': 'Erwin',
            'how_did_you_hear': '',
            'last_name': 'Johnson',
            'middle_name': 'Horace',
            'monthly_expenses': 1301,
            'monthly_income': 2465,
            'on_probation_parole': 'yes',
            'phone_number': '4153016005',
            'rap_outside_sf': 'no',
            'serving_sentence': 'yes',
            'being_charged': 'no',
            'ssn': '479928924',
            'us_citizen': 'yes',
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'consent_to_represent': 'yes',
            'understands_limits': 'yes',
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
            'email': 'cmrtestuser@gmail.com'
        }))
        self.assertFalse(form.is_valid())
        self.assertFalse('phone_number' in form.errors)
        self.assertFalse('email' in form.errors)
        self.assertFalse('address' in form.errors)

    def test_form_display(self):
        fake_answers = mock.FILLED_SF_DATA
        form = self.get_sf_form(fake_answers)
        self.assertTrue(form.is_valid())
        self.assertTrue(hasattr(form.display(), '__html__'))

    def test_dynamic_field_display_with_existing_field(self):
        fake_answers = mock.FILLED_SF_DATA
        form = self.get_sf_form(fake_answers)
        self.assertEqual(
            form.first_name_display, form.first_name.render(display=True))
        self.assertTrue(hasattr(form.first_name_display, '__html__'))

    def test_dynamic_field_display_with_nonexistent_field(self):
        fake_answers = mock.FILLED_SF_DATA
        form = self.get_sf_form(fake_answers)
        self.assertEqual(
            form.random_field_display, "")

    def test_dynamic_field_display_raises_error_for_unknown_attribute(self):
        fake_answers = mock.FILLED_SF_DATA
        form = self.get_sf_form(fake_answers)
        with self.assertRaises(AttributeError):
            str(form.foobar)

    def test_fields_inherit_skip_validation_parse_only(self):
        field_validator = Mock()
        form_validator = Mock()

        class SmallNumberField(IntegerField):
            context_key = 'number'
            validators = [field_validator]

        class ExampleForm(Form):
            fields = [SmallNumberField]
            validators = [form_validator]

        form = ExampleForm(
            dict(number='11'), skip_validation_parse_only=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(11, form.cleaned_data['number'])
        field_validator.assert_not_called()
        form_validator.assert_not_called()
