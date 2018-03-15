from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from intake.tests.factories import FormSubmissionWithOrgsFactory
from user_accounts.management.commands.alert_if_org_is_absent import Command
from user_accounts.tests.factories import UserFactory, \
    FakeOrganizationFactory, UserProfileFactory

over_1_month_ago = timezone.now() - timedelta(days=35)


class TestCommand(TestCase):

    def setUp(self):
        self.org = FakeOrganizationFactory(
            name="Alameda County Pubdef", is_live=True)
        self.user = UserFactory(last_login=over_1_month_ago)
        UserProfileFactory(user=self.user, organization=self.org)
        self.sub = FormSubmissionWithOrgsFactory(
            organizations=[self.org], answers={},
            date_received=over_1_month_ago)
        FormSubmissionWithOrgsFactory(
            organizations=[self.org], answers={},
            date_received=timezone.now())

    def run_command(self):
        command = Command()
        with self.settings(DEFAULT_HOST='localhost:8000'):
            command.handle()

    def test_unopened_application_older_than_1_month(self):
        self.run_command()
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        expected_subject = "Inactive organization on localhost:8000"
        expected_body = "Alameda County Pubdef has 2 unopened applications, " \
                        "the oldest from {}".format(
                            over_1_month_ago.strftime("%-m/%-d/%y"))
        self.assertEqual(expected_subject, email.subject)
        self.assertIn(expected_body, email.body)

    def test_unopened_application_newer_than_1_month(self):
        self.sub.date_received = timezone.now() - timedelta(days=29)
        self.sub.save()
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_no_logins_and_unopened_apps(self):
        self.user.last_login = None
        self.user.save()
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_logins_unopened_apps_and_org_not_live(self):
        self.org.is_live = False
        self.org.save()
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_logins_but_no_unopened_apps(self):
        self.sub.applications.update(has_been_opened=True)
        self.run_command()
        self.assertEqual(0, len(mail.outbox))
