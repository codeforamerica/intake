from unittest import TestCase as BaseTestCase
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from django.core import mail
from django.utils.http import urlencode
from django.conf import settings
from urllib import parse
import json


from intake.tests.mock import FormSubmissionFactory
from intake import notifications

class TestNotifications(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        from project.jinja2 import jinja_config
        jinja_config()

    def test_email(self):
        mail.send_mail(
            'Notification Test',
            'Hi',
            settings.MAIL_DEFAULT_SENDER,
            [settings.DEFAULT_NOTIFICATION_EMAIL]
            )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, settings.MAIL_DEFAULT_SENDER)

    @patch('intake.notifications.get_template')
    def test_email_notification_class(self, *args):
        from intake.notifications import EmailNotification
        default = EmailNotification("Hello {{name}}", "basic_email.txt")
        default.send(name="Ben")
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Hello Ben")


class TestSlack(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        class MockSub:
            id = 2
            def get_anonymous_display(self):
                return "Shining Koala"
            def __str__(self):
                return self.get_anonymous_display()
            def get_contact_preferences(self):
                return ["text message", "email"]
        cls.sub = MockSub()
        cls.user = Mock(email='staff@org.org')
        cls.request = Mock()
        cls.request.build_absolute_uri.return_value = "http://filled_pdf/"
        cls.submission_count = 101

    def test_render_new_submission(self):
        expected_new_submission_text = str(
"""New submission #101!
<http://filled_pdf/|Review it here>
They want to be contacted via text message and email
""")
        new_submission = notifications.slack_new_submission.render(
            submission=self.sub,
            submission_count=self.submission_count,
            request=self.request
            ).message

    def test_render_submission_viewed(self):
        expected_submission_viewed_text = str(
"""staff@org.org looked at Shining Koala's application""")
        submission_viewed = notifications.slack_submission_viewed.render(
            submission=self.sub, user=self.user
            ).message
        self.assertEqual(submission_viewed, expected_submission_viewed_text)
        
    def test_bundle_viewed(self):
        expected_bundle_viewed_text = str(
"""staff@org.org opened apps from Shining Koala, Shining Koala, and Shining Koala""")
        bundle_viewed = notifications.slack_bundle_viewed.render(
            user=self.user,
            submissions=[self.sub for i in range(3)]
            ).message
        self.assertEqual(bundle_viewed, expected_bundle_viewed_text)

    @patch('intake.notifications.requests.post')
    def test_slack_send(self, mock_post):
        mock_post.return_value = "HTTP response"
        expected_json = '{"text": "New submission #101!\\n&lt;http://filled_pdf/|Review it here&gt;\\nThey want to be contacted via text message and email\\n"}'
        expected_headers = {'Content-type': 'application/json'}
        response = notifications.slack_new_submission.send(
            submission=self.sub,
            submission_count=self.submission_count,
            request=self.request
            )
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(
            called_kwargs['data'], expected_json)
        self.assertDictEqual(
            called_kwargs['headers'], expected_headers)









