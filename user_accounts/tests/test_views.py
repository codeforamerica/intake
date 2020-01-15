from unittest.mock import patch

from django.core import mail
from django.test import TestCase

from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from django.urls import reverse
from project.fixtures_index import (
    ESSENTIAL_DATA_FIXTURES, MOCK_USER_ACCOUNT_FIXTURES
)


class TestUserProfileView(AuthIntegrationTestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES + MOCK_USER_ACCOUNT_FIXTURES

    def test_can_see_org_in_auth_bar(self):
        user = self.be_sfpubdef_user()
        response = self.client.get(reverse('user_accounts-profile'))
        self.assertContains(response, user.profile.organization.name)


class TestMailgunBouncedEmailView(TestCase):

    def post(self):
        # mailgun sends headers from the original message in a string
        # containing a list of key-value pair lists.
        fake_headers_string = '[' \
            '["Sender","bob.pubdef@clearmyrecord.org"],' \
            '["Subject","Clear My Record: Application updated"],' \
            '["Date","Yesterday"]' \
            ']'
        return self.client.post(
            reverse('user_accounts-mailgun_bounce'),
            {
                'recipient': "applicant@example.com",
                'error': "R. 000 Internet Permanently Broken",
                'message-headers': fake_headers_string,
                'token': 'i-am-a-secret-token',
                'timestamp': '12432543',
                'signature': 'Mother of Dragons, Breaker of Chains, Esq.'
            })

    @patch('intake.services.mailgun_api_service.hmac')
    def test_invalid_post_returns_404(self, mock_hmac):
        mock_hmac.compare_digest.return_value = False
        response = self.post()
        self.assertEqual(404, response.status_code)

    @patch('intake.services.mailgun_api_service.hmac')
    def test_valid_post_returns_200_and_sends_email(self, mock_hmac):
        mock_hmac.compare_digest.return_value = True
        response = self.post()
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEqual(['bob.pubdef@clearmyrecord.org'], sent_mail.to)
        self.assertIn('applicant@example.com', sent_mail.body)
        self.assertIn('Clear My Record: Application updated', sent_mail.body)
        self.assertIn('Yesterday', sent_mail.body)
        self.assertIn('R. 000 Internet Permanently Broken', sent_mail.body)
