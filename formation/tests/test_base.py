from unittest import TestCase
from unittest.mock import Mock, patch
from formation import base
from formation.tests import mock


class TestBindParseValidate(TestCase):

    def test_can_be_instantiated_without_data(self):
        unbound = base.BindParseValidate()
        self.assertEqual(unbound.raw_input_data, base.UNSET)
        self.assertEqual(unbound.is_bound(), False)
        self.assertEqual(unbound.context_key, 'no_context')
        self.assertDictEqual(unbound.errors, {})
        self.assertListEqual(unbound.validators, [])
        with self.assertRaises(NotImplementedError):
            unbound.is_valid()

    def test_can_be_instantiated_with_data(self):
        input_data = {}
        bound = base.BindParseValidate(input_data)
        self.assertEqual(bound.raw_input_data, input_data)
        self.assertEqual(bound.is_bound(), True)
        self.assertEqual(bound.is_valid(), True)
        self.assertEqual(bound.parsed_data, input_data)
        self.assertDictEqual(bound.errors, {})

    @patch('formation.base.BindParseValidate.parse_and_validate')
    def test_doesnt_run_parse_and_validate_until_is_valid_is_called(
            self, parse_and_validate):
        input_data = {}
        # set input during init
        bound = base.BindParseValidate(input_data)
        # shouldn't have run validation
        parse_and_validate.assert_not_called()
        # set input manually
        bound.bind(input_data)
        # shouldn't have run validation
        parse_and_validate.assert_not_called()
        # trigger parsing and validation
        self.assertEqual(bound.is_valid(), True)
        parse_and_validate.assert_called_once_with(input_data)

    def test_will_run_validators(self):
        input_data = {}
        validator = Mock()

        class MyForm(base.BindParseValidate):
            validators = [validator]

        form = MyForm(input_data)
        self.assertEqual(form.is_valid(), True)
        self.assertDictEqual(form.errors, {})
        validator.assert_called_once_with(input_data)

    def test_handles_simple_validator(self):
        form = mock.form_for_validator(mock.simple_validator)
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            base.DEFAULT_CONTEXT_KEY: [mock.sample_error_message]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_handles_context_validator(self):
        form = mock.form_for_validator(mock.context_validator)
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            "special": [mock.sample_error_message]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_handles_list_validator(self):
        form = mock.form_for_validator(mock.list_validator)
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            base.DEFAULT_CONTEXT_KEY: [
                mock.sample_error_message,
                mock.sample_error_message2
            ]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_handles_dict_validator(self):
        form = mock.form_for_validator(mock.dict_validator)
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            "special": [
                mock.sample_error_message
            ]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_handles_dict_with_list_validator(self):
        form = mock.form_for_validator(
            mock.dict_with_list_validator)
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            "special": [
                mock.sample_error_message,
                mock.sample_error_message2
            ]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_handles_django_validator(self):
        from django.core.validators import EmailValidator
        error_msg = 'Enter a valid email address.'
        form = mock.form_for_validator(
            EmailValidator(error_msg), mock.bad_email
        )
        self.assertEqual(form.is_valid(), False)
        expected_errors = {
            base.DEFAULT_CONTEXT_KEY: [
                error_msg
            ]
        }
        self.assertDictEqual(expected_errors, form.errors)

    def test_prefix(self):
        class Scoped(base.BindParseValidate):
            context_key = "bar"
        unbound = Scoped(prefix="foo")
        self.assertEqual(unbound.context_key, "foobar")

    def test_wont_run_validators_if_skip_validation_parse_only(self):
        input_data = {}
        validator = Mock()

        class MyForm(base.BindParseValidate):
            validators = [validator]

        form = MyForm(input_data, skip_validation_parse_only=True)
        self.assertEqual(form.is_valid(), True)
        self.assertDictEqual(form.errors, {})
        validator.assert_not_called()
