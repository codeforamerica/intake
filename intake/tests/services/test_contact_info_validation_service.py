from unittest.mock import patch, Mock
from django.conf import settings
from project.tests.testcases import TestCase
from intake.services.contact_info_validation_service import \
    validate_email_with_mailgun, mailgun_get_request
from intake.exceptions import MailgunAPIError


class TestMailGunGetRequest(TestCase):

    @patch('intake.services.contact_info_validation_service.requests.get')
    def test_passes_args_correctly(self, mock_requests_get):
        fake_url = 'https://example.com'
        query_params = dict(
            address='sample@example.com',
            mailbox_verification=True)
        mailgun_get_request(fake_url, query_params)
        call_args, keyword_args = mock_requests_get.call_args
        self.assertEqual(query_params, keyword_args['params'])
        auth = keyword_args['auth']
        self.assertEqual('api', auth.username)
        self.assertEqual(settings.MAILGUN_PRIVATE_API_KEY, auth.password)
        self.assertEqual(fake_url, call_args[0])


class TestValidateEmailWithMailgun(TestCase):

    @patch(
        'intake.services.contact_info_validation_service.mailgun_get_request')
    def test_known_valid_email(self, mock_mailgun_get):
        email = 'cmrtestuser@gmail.com'
        mock_mailgun_get.return_value = (
            200,
            {
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
        )    requests_patcher = patch(
        'intake.services.contact_info_validation_service.mailgun_get_request')
    requests_patcher.start()
    context.test.patches = {'requests_patcher': requests_patcher}
    context.test.patches = {}
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
