from unittest import TestCase
from unittest.mock import Mock, patch

from formation import field_base, base, exceptions
from formation.tests import mock
from formation.tests.utils import PatchTranslationTestCase


class TestField(PatchTranslationTestCase):

    empty_values = ['', base.UNSET, None]
    empty = {}
    not_empty = {'my_field': 'something'}
    required_error = {
        "my_field": ["This field is required."]
        }
    recommended_warning = recommended_warning = {
        "my_field": ["Leaving this field blank might cause problems."]
        }

    def get_example_subclass(self):

        class MyField(field_base.Field):
            context_key = "my_field"
            empty_value = ""

            def parse(inst, raw_value):
                value = inst.empty_value
                if raw_value:
                    value = raw_value
                return value

        return MyField


    def test_init(self):
        field = field_base.Field()
        self.assertFalse(field.is_multivalue)
        self.assertEqual(field.context_key, base.DEFAULT_CONTEXT_KEY)
        self.assertEqual(field.get_input_name(), base.DEFAULT_CONTEXT_KEY)
        self.assertEqual(
            field.get_html_class_name(), base.DEFAULT_CONTEXT_KEY)
        self.assertFalse(field.is_bound())
        with self.assertRaises(NotImplementedError):
            field.is_valid()  

    def test_init_with_data(self):
        data = {
            "no_context": "some data"
        }
        field = field_base.Field(data)
        self.assertTrue(field.is_bound())
        self.assertTrue(field.is_valid())
        self.assertDictEqual(
            field.raw_input_data, data)
        self.assertEqual(
            field.raw_input_value, "some data")
        self.assertEqual(
            field.parsed_data, "some data")

    def test_basic_inheritance(self):
        MyField = self.get_example_subclass()
        field = MyField()
        self.assertEqual(field.get_input_name(), "my_field")

    def test_defaults_to_required(self):
        field = field_base.Field({})
        self.assertEqual(field.required, True)

    def test_defaults_to_recommended_false(self):
        field = field_base.Field({})
        self.assertEqual(field.recommended, False)

    def test_adds_required_error_if_unset(self):
        # this one is having trouble with translation
        field = field_base.Field({})
        self.assertEqual(field.is_valid(), False)
        expected_error_message = "This field is required."
        error_message = field.errors['no_context'].pop()
        # must be cast as string to evaluate the lazy translation string
        self.assertEqual(str(error_message), expected_error_message)
    
    def test_adds_required_error_if_gets_empty_values(self):
        # make a subclass that has a custom empty value
        MyField = self.get_example_subclass()

        for empty_value in self.empty_values:
            field = MyField({'my_field': empty_value})
            self.assertEqual(field.is_valid(), False)
            expected_errors = {
                "my_field": ["This field is required."]
            }
            self.assertEqual(field.errors, expected_errors)

    def test_no_required_errors_if_not_required(self):
        MyField = self.get_example_subclass()
        for empty_value in self.empty_values:
            field = MyField({'my_field': empty_value}, required=False)
            self.assertEqual(field.is_valid(), True)
            expected_errors = {}
            self.assertDictEqual(field.errors, expected_errors)

    def test_assert_parse_received_correct_type(self):
        MyField = self.get_example_subclass()
        field = MyField()
        with self.assertRaises(TypeError):
            field.assert_parse_received_correct_type(2, str)
        with self.assertRaises(TypeError):
            field.assert_parse_received_correct_type("invalid", list)
        # should not raise any error
        field.assert_parse_received_correct_type("valid", str)
        field.assert_parse_received_correct_type(["valid"], list)

    def test_recommended_required_empty_returns_required_error_only(self):
        MyField = self.get_example_subclass()
        field = MyField(self.empty, recommended=True, required=True)
        self.assertFalse(field.is_valid())
        self.assertFalse(field.warnings)
        self.assertDictEqual(field.errors, self.required_error)

    def test_recommended_empty_returns_recommended_warning_only(self):
        MyField = self.get_example_subclass()
        field = MyField(self.empty, recommended=True, required=False)
        self.assertTrue(field.is_valid())
        self.assertFalse(field.errors)
        self.assertDictEqual(field.warnings, self.recommended_warning)

    def test_recommended_not_empty_has_no_warnings_or_errors(self):
        MyField = self.get_example_subclass()
        field = MyField(self.not_empty, recommended=True, required=False)
        self.assertTrue(field.is_valid())
        self.assertFalse(field.errors)
        self.assertFalse(field.warnings)

    def test_recommended_required_not_empty_has_no_warnings_or_errors(self):
        MyField = self.get_example_subclass()
        field = MyField(self.not_empty, recommended=True, required=True)
        self.assertTrue(field.is_valid())
        self.assertFalse(field.errors)
        self.assertFalse(field.warnings)
        
    def test_recommended_empty_extra_validator_returns_recommended_warning_only(self):
        from formation.fields import EmailField
        field = EmailField(self.empty, recommended=True, required=False)
        self.assertTrue(field.is_valid())
        self.assertFalse(field.errors)
        self.assertDictEqual(field.warnings, {
            "email": ["Leaving this field blank might cause problems."]

        })



