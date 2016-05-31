from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from django.core import mail
from django.conf import settings


from intake.tests.mock import FormSubmissionFactory

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

    def test_new_application_email(self):
        from intake.notifications import new_submission_email
        submission = FormSubmissionFactory.create()
        new_submission_email.send(
            request=Mock(),
            submission=submission
            )



