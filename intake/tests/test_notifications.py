from unittest import TestCase as BaseTestCase
from unittest.mock import Mock, patch
from django.test import TestCase
from django.test import override_settings
from project.jinja2 import external_reverse
from django.core import mail
from django.conf import settings
import json


from intake.tests import mock, factories

from intake import notifications


notification_mock_settings = dict(
    FRONT_API_TOKEN='mytoken',
    FRONT_EMAIL_CHANNEL_ID='email_ch',
    FRONT_PHONE_CHANNEL_ID='phone_ch',
    SLACK_WEBHOOK_URL='slack',
    CELERY_TASK_ALWAYS_EAGER=True
)


class TestNotifications(TestCase):

    def setUp(self):
        TestCase.setUp(self)

    def test_email(self):
        mail.send_mail(
            'Notification Test',
            'Hi',
            settings.MAIL_DEFAULT_SENDER,
            ['pegasus@flying.horse']
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.MAIL_DEFAULT_SENDER)

    @patch('intake.notifications.loader.get_template')
    def test_email_notification_class(self, *args):
        from intake.notifications import EmailNotification
        default = EmailNotification("Hello {{name}}", "basic_email.txt")
        default.send(name="Ben", to=['pegasus@flying.horse'])
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Hello Ben")

    @patch('intake.tasks.request')
    @patch('intake.notifications.loader.get_template')
    @override_settings(DIVERT_REMOTE_CONNECTIONS=False,
                       **notification_mock_settings)
    def test_front_notifications(self, get_template, mock_post):
        # check all the basics using an SMS example
        mock_post.return_value = mock.FrontSendMessageResponse.success()
        from intake.notifications import jinja
        get_template.return_value = jinja.env.from_string(
            "{{message}} can you read me?")

        front_text = notifications.FrontSMSNotification(
            body_template_path="front_body_template.txt"
        )

        front_text.channel_id = 'phone_id'

        front_text.send(
            to=["+15555555555"],
            message="Hey Ben")

        expected_data = {
            'body': "Hey Ben can you read me?",
            'text': "Hey Ben can you read me?",
            'to': ["+15555555555"],
            'options': {
                'archive': True
            }
        }
        expected_headers = {
            'Authorization': 'Bearer mytoken',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        self.assertTrue(mock_post.called)
        post_kwargs = [*mock_post.call_args][1]
        posted_data = json.loads(post_kwargs['data'])
        self.assertDictEqual(posted_data, expected_data)
        self.assertDictEqual(post_kwargs['headers'], expected_headers)
        self.assertEqual(
            post_kwargs['url'],
            'https://api2.frontapp.com/channels/phone_id/messages')

        # check the front email works as expected
        mock_post.reset_mock()
        mock_post.return_value = mock.FrontSendMessageResponse.success()
        get_template.return_value = jinja.env.from_string(
            "{{message}} this is an email message body.")

        front_email = notifications.FrontEmailNotification(
            subject_template="Front test",
            body_template_path="front_body_template.txt"
        )
        front_email.channel_id = 'email_id'

        front_email.send(
            to=["cmrtestuser@gmail.com"],
            message="Hi")
        expected_data.update({
            'to': ["cmrtestuser@gmail.com"],
            'subject': 'Front test',
            'body': 'Hi this is an email message body.',
            'text': 'Hi this is an email message body.',
        })
        self.assertTrue(mock_post.called)
        post_kwargs = [*mock_post.call_args][1]
        posted_data = json.loads(post_kwargs['data'])
        self.assertDictEqual(posted_data, expected_data)
        self.assertDictEqual(post_kwargs['headers'], expected_headers)
        self.assertEqual(
            post_kwargs['url'],
            'https://api2.frontapp.com/channels/email_id/messages')


class TestSlackAndFront(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        class MockSub:
            id = 2

            def get_anonymous_display(self):
                return "Shining Koala"

            def __str__(self):
                return self.get_anonymous_display()

            def get_nice_contact_preferences(self):
                return ["text message", "email"]

            def get_nice_counties(self):
                return ['San Francisco', 'Contra Costa']
        cls.sub = MockSub()
        cls.user = Mock(email='staff@org.org')
        cls.request = Mock()
        cls.request.build_absolute_uri.return_value = "http://filled_pdf/"
        cls.submission_count = 101

    @patch('intake.tasks.request')
    @override_settings(DIVERT_REMOTE_CONNECTIONS=False,
                       **notification_mock_settings)
    def test_slack_simple(self, mock_post):
        mock_post.return_value = "HTTP response"
        expected_json = '{"text": "Hello slack <&>"}'
        expected_headers = {'Content-type': 'application/json'}
        notifications.slack_simple.send("Hello slack <&>")
        self.assertTrue(mock_post.called)
        called_kwargs = [*mock_post.call_args][1]
        self.assertEqual(
            called_kwargs['data'], expected_json)
        self.assertDictEqual(
            called_kwargs['headers'], expected_headers)
