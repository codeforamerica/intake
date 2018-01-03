from unittest.mock import patch, Mock
from django.conf import settings
from django.test import TestCase, override_settings
from intake.services.mailgun_api_service import \
    validate_email_with_mailgun, mailgun_get_request, send_mailgun_email, \
    MAILGUN_MESSAGES_API_URL, set_route_for_user_profile, \
    MAILGUN_ROUTES_API_URL
from intake.exceptions import MailgunAPIError
from user_accounts.tests.factories import \
    FakeOrganizationFactory, UserProfileFactory, UserFactory


class TestMailGunGetRequest(TestCase):

    @patch('intake.services.mailgun_api_service.requests.get')
    def test_passes_args_correctly_when_run(self, mock_requests_get):
        fake_url = 'https://example.com'
        query_params = dict(
            address='sample@example.com',
            mailbox_verification=True)
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=True):
            mailgun_get_request(fake_url, query_params)
        call_args, keyword_args = mock_requests_get.call_args
        self.assertEqual(query_params, keyword_args['params'])
        auth = keyword_args['auth']
        self.assertEqual('api', auth[0])
        self.assertEqual(
            getattr(settings, 'MAILGUN_PRIVATE_API_KEY', ''), auth[1])
        self.assertEqual(fake_url, call_args[0])

    @patch('intake.services.mailgun_api_service.requests.get')
    def test_feature_flag_off_diverts_as_expected(self, mock_requests_get):
        expected_result = (
            200, dict(is_valid=True, mailbox_verification='true'))
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=False):
            result = mailgun_get_request('anything', query_params={})
        mock_requests_get.assert_not_called()
        self.assertEqual(expected_result, result)

    @override_settings()
    @patch('intake.services.mailgun_api_service.requests.get')
    def test_missing_setting_diverts_as_expected(self, mock_requests_get):
        expected_result = (
            200, dict(is_valid=True, mailbox_verification='true'))
        del settings.ALLOW_REQUESTS_TO_MAILGUN
        result = mailgun_get_request('anything', query_params={})
        mock_requests_get.assert_not_called()
        self.assertEqual(expected_result, result)

    @patch('intake.services.mailgun_api_service.requests.get')
    def test_when_response_is_empty(self, mock_requests_get):
        fake_url = 'https://example.com'
        query_params = dict(
            address='sample@example.com',
            mailbox_verification=True)
        mock_denied_response = Mock(content=b'', status_code=410)
        mock_requests_get.return_value = mock_denied_response
        expected_result = (410, None)
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=True):
            result = mailgun_get_request(fake_url, query_params)
        self.assertEqual(expected_result, result)
        mock_denied_response.json.assert_not_called()


class TestValidateEmailWithMailgun(TestCase):

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
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
                    "local_part": "cmrtestuser"}})
        expected_response = (True, None)
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
    def test_email_with_domain_typo(self, mock_mailgun_get):
        email = 'cmrtestuser@gmial.com'
        mock_mailgun_get.return_value = (
            200,
            {
                'address': 'cmrtestuser@gmial.com',
                'did_you_mean': 'cmrtestuser@gmail.com',
                'is_disposable_address': False,
                'is_role_address': False,
                'is_valid': False,
                'mailbox_verification': 'unknown',
                'parts': {
                    'display_name': None,
                    'domain': None,
                    'local_part': None}})
        expected_response = (False, 'cmrtestuser@gmail.com')
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
    def test_nonexistent_email_with_valid_format(self, mock_mailgun_get):
        email = 'notreal@codeforamerica.org'
        mock_mailgun_get.return_value = (
            200,
            {
                'address': 'notreal@codeforamerica.org',
                'did_you_mean': None,
                'is_disposable_address': False,
                'is_role_address': False,
                'is_valid': True,
                'mailbox_verification': 'false',
                'parts': {
                    'display_name': None,
                    'domain': 'codeforamerica.org',
                    'local_part': 'notreal'}})
        expected_response = (False, None)
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
    def test_invalid_email(self, mock_mailgun_get):
        email = 'ovinsbf'
        mock_mailgun_get.return_value = (
            200,
            {
                'address': 'ovinsbf',
                'did_you_mean': None,
                'is_disposable_address': False,
                'is_role_address': False,
                'is_valid': False,
                'mailbox_verification': 'false',
                'parts': {
                    'display_name': None,
                    'domain': None,
                    'local_part': None}})
        expected_response = (False, None)
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
    def test_valid_email_with_unknown_confirmation(self, mock_mailgun_get):
        email = 'ovinsbf'
        mock_mailgun_get.return_value = (
            200,
            {
                'address': 'something@yahoo.com',
                'did_you_mean': None,
                'is_disposable_address': False,
                'is_role_address': False,
                'is_valid': True,
                'mailbox_verification': 'unknown',
                'parts': {
                    'display_name': None,
                    'domain': None,
                    'local_part': None}})
        expected_response = (True, None)
        self.assertEqual(
            expected_response,
            validate_email_with_mailgun(email))

    @patch('intake.services.mailgun_api_service.mailgun_get_request')
    def test_mailgun_api_error(self, mock_mailgun_get):
        mock_mailgun_get.return_value = (403, {})
        with self.assertRaises(MailgunAPIError):
            validate_email_with_mailgun('')


class TestSendMailGunEmail(TestCase):
    fixtures = ['groups']

    def setUp(self):
        super().setUp()
        org = FakeOrganizationFactory(slug='yolo')
        self.profile = UserProfileFactory(
            organization=org,
            name='Jane Doe',
            user=UserFactory(
                username="jdoe", email='jane.doe@example.com')
        )

    @patch('intake.services.mailgun_api_service.tasks')
    @patch('intake.services.mailgun_api_service.mailgun_auth')
    def test_calls_async_and_passes_correct_args(
            self, mock_mailgun_auth, mock_tasks):
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=True):
            send_mailgun_email(
                'foo@bar.com', 'hello foo', self.profile, 'Hello')
        mock_tasks.celery_request.assert_called_once_with(
            'POST', MAILGUN_MESSAGES_API_URL,
            auth=mock_mailgun_auth.return_value, data={
                "from": "Jane Doe <jdoe.yolo@clearmyrecord.org>",
                "to": ['foo@bar.com'],
                "subject": 'Hello',
                "text": 'hello foo'
            }
        )

    @override_settings()
    @patch('intake.services.mailgun_api_service.tasks')
    def test_doesnt_run_without_setting_true(self, mock_tasks):
        del settings.ALLOW_REQUESTS_TO_MAILGUN
        result = send_mailgun_email(
            'foo@bar.com', 'hello foo', self.profile, 'Hello')
        mock_tasks.assert_not_called()
        self.assertEqual({}, result)


class TestSetRouteForUserProfile(TestCase):
    fixtures = ['groups']

    def setUp(self):
        super().setUp()
        org = FakeOrganizationFactory(slug='yolo')
        self.profile = UserProfileFactory(
            organization=org,
            name='Jane Doe',
            user=UserFactory(
                username="jdoe", email='jane.doe@example.com')
        )

    @patch('intake.services.mailgun_api_service.requests')
    @patch('intake.services.mailgun_api_service.mailgun_auth')
    def test_sends_request_to_mailgun_to_create_route_for_user(
            self, mock_mailgun_auth, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_requests.post.return_value = mock_response
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=True):
            set_route_for_user_profile(self.profile)
        mock_requests.post.assert_called_once_with(
            MAILGUN_ROUTES_API_URL, auth=mock_mailgun_auth.return_value,
            data={
                'priority': 0,
                'expression':
                    'match_recipient("jdoe.yolo@clearmyrecord.org")',
                'action': 'forward("jane.doe@example.com")'
            }
        )

    @patch('intake.services.mailgun_api_service.requests')
    def test_errors_if_not_200(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = None
        mock_requests.post.return_value = mock_response
        with self.settings(ALLOW_REQUESTS_TO_MAILGUN=True):
            with self.assertRaises(MailgunAPIError):
                set_route_for_user_profile(self.profile)

    @override_settings()
    @patch('intake.services.mailgun_api_service.requests')
    def test_doesnt_run_without_setting_true(self, mock_requests):
        del settings.ALLOW_REQUESTS_TO_MAILGUN
        result = set_route_for_user_profile(self.profile)
        mock_requests.assert_not_called()
        self.assertEqual({}, result)
