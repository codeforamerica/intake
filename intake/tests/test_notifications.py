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
            to=["bgolder@codeforamerica.org"],
            message="Hi")
        expected_data.update({
            'to': ["bgolder@codeforamerica.org"],
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

    def test_render_new_submission(self):
        expected_new_submission_text = str(
            """New submission #101 to San Francisco and Contra Costa!
<http://filled_pdf/|Shining Koala>
They want to be contacted via text message and email
""")
        new_submission = notifications.slack_new_submission.render(
            submission=self.sub,
            submission_count=self.submission_count,
            request=self.request
        ).message
        self.assertEqual(new_submission, expected_new_submission_text)

    def test_render_submission_viewed(self):
        expected_submission_viewed_text = str(
            """staff@org.org opened <url|Shining Koala's application>""")
        submission_viewed = notifications.slack_submissions_viewed.render(
            user=self.user,
            submissions=[self.sub],
            bundle_url='url',
        ).message
        self.assertEqual(submission_viewed, expected_submission_viewed_text)

    def test_render_submissions_viewed(self):
        expected_submissions_viewed_text = str(
            "staff@org.org opened apps from <url|Shining Koala, Shining "
            "Koala, and Shining Koala>")
        submissions_viewed = notifications.slack_submissions_viewed.render(
            user=self.user,
            submissions=[self.sub for i in range(3)],
            bundle_url='url',
        ).message
        self.assertEqual(submissions_viewed, expected_submissions_viewed_text)

    def test_render_submission_deleted(self):
        expected_submission_deleted_text = str(
            """staff@org.org deleted <url|Shining Koala's application>""")
        deleted = notifications.slack_submissions_deleted.render(
            user=self.user,
            submissions=[self.sub],
            bundle_url='url',
        ).message
        self.assertEqual(deleted, expected_submission_deleted_text)

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

    @patch('intake.tasks.request')
    @override_settings(DIVERT_REMOTE_CONNECTIONS=False,
                       **notification_mock_settings)
    def test_slack_send(self, mock_post):
        mock_post.return_value = "HTTP response"
        expected_json = str(
            '{"text": "New submission #101 to San Francisco and Contra '
            'Costa!\\n<http://filled_pdf/|Shining Koala>\\nThey want to be '
            'contacted via text message and email\\n"}')
        expected_headers = {'Content-type': 'application/json'}
        notifications.slack_new_submission.send(
            submission=self.sub,
            submission_count=self.submission_count,
            request=self.request
        )
        self.assertTrue(mock_post.called)
        called_kwargs = [*mock_post.call_args][1]
        self.assertEqual(
            called_kwargs['data'], expected_json)
        self.assertDictEqual(
            called_kwargs['headers'], expected_headers)

    def test_render_slack_notification_sent(self):
        submission = factories.FormSubmissionFactory.build(
            anonymous_name="App")

        # case: email, sms
        expected = str(
            "Successfully sent a ping to App via email\nSuccessfully "
            "sent a ping to App via sms\n")
        methods = ['email', 'sms']
        result = notifications.slack_notification_sent.render(
            notification_type='ping',
            submission=submission, methods=methods).message
        self.assertEqual(expected, result)

        # case: snailmail, voicemail
        expected = str(
            "Did not send a ping to App via snailmail\nDid not send a "
            "ping to App via voicemail\n")
        methods = ['snailmail', 'voicemail']
        result = notifications.slack_notification_sent.render(
            notification_type='ping',
            submission=submission, methods=methods).message
        self.assertEqual(expected, result)

        # case: email, sms, snailmail, voicemail
        expected = "\n".join([
            "Successfully sent a ping to App via email",
            "Successfully sent a ping to App via sms",
            "Did not send a ping to App via snailmail",
            "Did not send a ping to App via voicemail\n"])
        methods = ['email', 'sms', 'snailmail', 'voicemail']
        result = notifications.slack_notification_sent.render(
            notification_type='ping',
            submission=submission, methods=methods).message
        self.assertEqual(expected, result)

    def test_render_slack_notification_failed(self):
        submission = factories.FormSubmissionFactory.build(
            anonymous_name="App")
        errors = Mock(**{
            'items.return_value': [
                ("email", "some errors"),
                ("sms", "more errors")
            ],
            'keys.return_value': ['email', 'sms']
        })
        expected = """ping by email and sms for App failed with errors:
```
email:
    some errors

sms:
    more errors
```"""
        result = notifications.slack_notification_failed.render(
            notification_type='ping',
            submission=submission, errors=errors).message
        self.assertEqual(expected, result)
