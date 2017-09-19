from unittest.mock import patch, Mock
from django.test import TestCase
from intake.services.contact_info_validation_service import \
    validate_email_with_mailgun
from intake.exceptions import MailgunAPIError


class TestValidateEmailWithMailgun(TestCase):

    @patch('intake.services.contact_info_validation_service.requests')
    def test_known_valid_email(self, mock_requests):
        email = 'cmrtestuser@gmail.com'
        mock_mailgun_response = {
            "address": "cmrtestuser@gmail.com",
            "did_you_mean": None,
            "is_disposable_address": False,
            "is_role_address": False,
            "is_valid": True,
            "mailbox_verification": 'true',
            "parts": {
                "display_name": None,
                "domain": "gmail.com",
                "local_part": "cmrtestuser"
            }
        }
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = mock_mailgun_response
        mock_requests.get.return_value = mock_response
        expected_response = (True, None)
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.contact_info_validation_service.requests')
    def test_email_with_domain_typo(self, mock_requests):
        email = 'cmrtestuser@gmial.com'
        mock_mailgun_response = {
            'address': 'cmrtestuser@gmial.com',
            'did_you_mean': 'cmrtestuser@gmail.com',
            'is_disposable_address': False,
            'is_role_address': False,
            'is_valid': False,
            'mailbox_verification': 'unknown',
            'parts': {
                'display_name': None,
                'domain': None,
                'local_part': None
            }
        }
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = mock_mailgun_response
        mock_requests.get.return_value = mock_response
        expected_response = (False, 'cmrtestuser@gmail.com')

        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.contact_info_validation_service.requests')
    def test_nonexistent_email_with_valid_format(self, mock_requests):
        email = 'notreal@codeforamerica.org'
        mock_mailgun_response = {
            'address': 'notreal@codeforamerica.org',
            'did_you_mean': None,
            'is_disposable_address': False,
            'is_role_address': False,
            'is_valid': True,
            'mailbox_verification': 'false',
            'parts': {
                'display_name': None,
                'domain': 'codeforamerica.org',
                'local_part': 'notreal'
            }
        }
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = mock_mailgun_response
        mock_requests.get.return_value = mock_response
        expected_response = (False, None)

        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.contact_info_validation_service.requests')
    def test_invalid_email(self, mock_requests):
        email = 'ovinsbf'
        mock_mailgun_response = {
            'address': 'ovinsbf',
            'did_you_mean': None,
            'is_disposable_address': False,
            'is_role_address': False,
            'is_valid': False,
            'mailbox_verification': 'unknown',
            'parts': {
                'display_name': None,
                'domain': None,
                'local_part': None
            }
        }
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = mock_mailgun_response
        mock_requests.get.return_value = mock_response
        expected_response = (False, None)

        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.contact_info_validation_service.requests')
    def test_mailgun_api_error(self, mock_requests):
        mock_response = Mock(status_code=403)
        mock_requests.get.return_value = mock_response
        with self.assertRaises(MailgunAPIError):
            validate_email_with_mailgun('')
