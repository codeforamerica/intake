from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from intake.tests.factories import FormSubmissionWithOrgsFactory
from user_accounts.management.commands.alert_if_org_is_absent import Command
from user_accounts.tests.factories import UserFactory, \
    FakeOrganizationFactory, UserProfileFactory

old_login_date = timezone.now() - timedelta(days=21)
recent_login_date = timezone.now() - timedelta(days=19)


class TestCommand(TestCase):

    def setUp(self):
        self.org = FakeOrganizationFactory(
            name="Alameda County Pubdef", is_live=True)
        self.sub = FormSubmissionWithOrgsFactory(
            organizations=[self.org], answers={})

    def run_command(self):
        command = Command()
        with self.settings(DEFAULT_HOST='localhost:8000'):
            command.handle()

    def test_alerts_with_old_logins_and_unopened_apps(self):
        user1 = UserFactory(last_login=old_login_date)
        user2 = UserFactory(last_login=old_login_date - timedelta(days=2))
        user3 = UserFactory(last_login=None)
        UserProfileFactory(user=user1, organization=self.org)
        UserProfileFactory(user=user2, organization=self.org)
        UserProfileFactory(user=user3, organization=self.org)
        self.run_command()
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        expected_subject = "Inactive organization on localhost:8000"
        expected_body = "Alameda County Pubdef has not logged in since " \
                        "{} and has 1 unopened applications".format(
                            old_login_date.strftime("%a %b %-d %Y"))
        self.assertEqual(expected_subject, email.subject)
        self.assertIn(expected_body, email.body)

    def test_no_alert_with_no_logins_and_unopened_apps(self):
        user1 = UserFactory(last_login=None)
        user2 = UserFactory(last_login=None)
        UserProfileFactory(user=user1, organization=self.org)
        UserProfileFactory(user=user2, organization=self.org)
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_old_logins_unopened_apps_and_org_not_live(self):
        user1 = UserFactory(last_login=old_login_date)
        user2 = UserFactory(last_login=old_login_date - timedelta(days=2))
        user3 = UserFactory(last_login=None)
        self.org.is_live = False
        self.org.save()
        UserProfileFactory(user=user1, organization=self.org)
        UserProfileFactory(user=user2, organization=self.org)
        UserProfileFactory(user=user3, organization=self.org)
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_old_logins_but_no_unopened_apps(self):
        user1 = UserFactory(last_login=old_login_date)
        user2 = UserFactory(last_login=old_login_date - timedelta(days=2))
        user3 = UserFactory(last_login=None)
        UserProfileFactory(user=user1, organization=self.org)
        UserProfileFactory(user=user2, organization=self.org)
        UserProfileFactory(user=user3, organization=self.org)
        self.sub.applications.update(has_been_opened=True)
        self.run_command()
        self.assertEqual(0, len(mail.outbox))

    def test_no_alert_with_recent_logins_and_unopened_apps(self):
        user1 = UserFactory(last_login=recent_login_date)
        user2 = UserFactory(last_login=old_login_date)
        user3 = UserFactory(last_login=None)
        UserProfileFactory(user=user1, organization=self.org)
        UserProfileFactory(user=user2, organization=self.org)
        UserProfileFactory(user=user3, organization=self.org)
        self.run_command()
        self.assertEqual(0, len(mail.outbox))
