import logging

from django.core.exceptions import ValidationError
from django.test import TestCase

from formation.fields import EmailField, PhoneNumberField
from formation.tests.utils import PatchTranslationTestCase
from formation.form_base import Form
from unittest.mock import patch

from formation.validators import at_least_email_or_phone, \
    AtLeastEmailOrPhoneValidator, \
    mailgun_email_validator
from intake.exceptions import MailgunAPIError
from project.tests.assertions import assertInLogs


class TestValidChoiceValidator(PatchTranslationTestCase):

    def test_raises_error_if_no_choices_on_context(self):
        # use with a CharField
        pass

    def test_no_errors_if_empty_and_not_required(self):
        pass

    def test_errors_if_required_and_empty(self):
        pass

    def test_errors_if_invalid_choice(self):
        pass

    def test_creates_expected_error_message(self):
        pass

    def test_creates_expected_possible_choices(self):
        pass


class TestMultipleValidChoiceValidator(PatchTranslationTestCase):

    def test_creates_expected_error_message(self):
        pass

    def test_raises_error_if_not_choices_on_context(self):
        pass

    def test_errors_for_any_invalid_choices(self):
        pass


class EmailAndPhoneForm(Form):
    fields = [
        PhoneNumberField,
        EmailField
    ]
    validators = [
        at_least_email_or_phone
    ]


class TestAtLeastEmailOrTextValidator(TestCase):

    def test_valid_if_both_values(self):
        form = EmailAndPhoneForm(dict(
            email='hello@nowhere.com',
            phone_number='415-444-4444'
        ))
        self.assertTrue(form.is_valid())

    def test_valid_if_missing_only_email(self):
        form = EmailAndPhoneForm(dict(
            phone_number='415-444-4444'
        ))
        self.assertTrue(form.is_valid())

    def test_valid_if_missing_only_phone(self):
        form = EmailAndPhoneForm(dict(
            email='hello@nowhere.com'
        ))
        self.assertTrue(form.is_valid())

    def test_errors_if_missing_both(self):
        form = EmailAndPhoneForm({})
        self.assertFalse(form.is_valid())
        expected_errors = {
            key: [AtLeastEmailOrPhoneValidator.message]
            for key
            in AtLeastEmailOrPhoneValidator.field_keys
        }
        self.assertDictEqual(form.errors, expected_errors)


@patch('formation.validators.validate_email_with_mailgun')
class TestMailgunEmailValidator(TestCase):
    def test_valid_if_mailgun_returns_valid(self, mock_mailgun_service):
        mock_mailgun_service.return_value = (True, None)
        try:
            mailgun_email_validator('sample@example.com')
        except ValidationError as err:
            raise AssertionError('unexpectedly raised {}'.format(err))

    def test_invalid_if_mailgun_returns_invalid(self, mock_mailgun_service):
        mock_mailgun_service.return_value = (False, None)
        with self.assertRaises(ValidationError) as context:
            mailgun_email_validator('sample@example.com')

        expected_message = 'The email address you entered does not ' \
                           'appear to exist.'
        self.assertEqual(expected_message, str(context.exception.message))

    def test_updates_error_message_if_mailgun_returns_suggestion(
            self, mock_mailgun_service):
        mock_mailgun_service.return_value = (False, "sample@example.com")
        with self.assertRaises(ValidationError) as context:
            mailgun_email_validator('sample@example.co')

        expected_message = 'The email address you entered does not ' \
                           'appear to exist. Did you mean sample@example.com?'
        self.assertEqual(expected_message, str(context.exception.message))

    def test_valid_if_mailgun_api_error(self, mock_mailgun_service):
        mock_mailgun_service.side_effect = MailgunAPIError(
            "Mailgun responded with 404")
        try:
            mailgun_email_validator('sample@example.com')
        except Exception as err:
            raise AssertionError('unexpectedly raised {}'.format(err))

    @patch('formation.validators.send_email_to_admins')
    def test_notifies_admin_if_mailgun_api_error(
                self, mock_email_admins, mock_mailgun_service):
        mock_mailgun_service.side_effect = MailgunAPIError(
            "Mailgun responded with 404")
        with self.assertLogs(
                'project.services.logging_service', logging.ERROR) as logs:
            mailgun_email_validator('sample@example.com')
        assertInLogs(logs, 'mailgun_api_error')
        self.assertEqual(1, len(mock_email_admins.mock_calls))
