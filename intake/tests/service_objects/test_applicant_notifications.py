from unittest.mock import patch, Mock
from django.test import TestCase
from user_accounts.models import Organization
from intake.constants import Organizations
from intake.tests import mock
from intake.tests.services.test_followups import get_old_date
from intake.service_objects import applicant_notifications
from intake.service_objects.applicant_notifications import (
    EMAIL, SMS, VOICEMAIL, SNAILMAIL)
from intake import utils, models


class TestApplicantNotification(TestCase):

    fixtures = [
        'counties',
        'organizations'
    ]

    class_under_test = applicant_notifications.ApplicantNotification

    def many_orgs(self):
        orgs = list(Organization.objects.filter(
                    slug__in=[
                        Organizations.ALAMEDA_PUBDEF,
                        Organizations.SF_PUBDEF,
                        Organizations.MONTEREY_PUBDEF]))
        orgs = utils.sort_orgs_in_default_order(orgs)
        return orgs

    def make_full_submission(self, orgs, **answer_overrides):
        applicant = models.Applicant()
        applicant.save()
        answers = mock.fake.all_county_answers(
            first_name="Hubert",
            contact_preferences=[
                'prefers_email',
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'
            ],
            email='test@gmail.com',
            phone_number='5554442222',
        )
        answers.update(answer_overrides)
        return mock.FormSubmissionFactory.create(
            date_received=get_old_date(),
            anonymous_name="Cerulean Beetle",
            organizations=orgs,
            answers=answers,
            applicant=applicant
        )

    def org_notification_and_default_sub(self, **answer_overrides):
        orgs = self.many_orgs()
        sub = self.make_full_submission(orgs, **answer_overrides)
        notification = self.class_under_test(sub)
        return orgs, sub, notification


class TestApplicantNotificationParentClass(TestApplicantNotification):

    @patch('intake.utils.get_random_staff_name')
    def test_builds_correct_context(self, staff_name):
        staff_name.return_value = "Marzipan"
        orgs, sub, notification = self.org_notification_and_default_sub()
        county_names = [org.county.name for org in orgs]
        org_names = [org.name for org in orgs]

        context = notification.get_context()

        self.assertEqual("Hubert", context['name'])
        self.assertEqual("Marzipan", context['staff_name'])
        self.assertEqual(county_names, context['county_names'])
        self.assertEqual(orgs, context['organizations'])
        self.assertEqual(org_names, context['organization_names'])


class TestFollowupNotification(TestApplicantNotification):

    class_under_test = applicant_notifications.FollowupNotification

    def test_builds_correct_context_for_email(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        messages = [org.long_followup_message for org in orgs]

        context = notification.get_context(EMAIL)

        self.assertEqual(messages, context['followup_messages'])

    def test_builds_correct_context_for_sms(self):
        orgs, sub, notification = self.org_notification_and_default_sub(
            contact_preferences=[
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'],
            phone_number='5554442222',
            )
        messages = [org.short_followup_message for org in orgs]

        context = notification.get_context(SMS)

        self.assertEqual(messages, context['followup_messages'])

    def test_set_contact_method_for_email(self):
        methods = [EMAIL]
        orgs, sub, notification = self.org_notification_and_default_sub()

        notification.set_contact_methods()
        self.assertEqual(methods, notification.contact_methods)

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_logs_one_followup_event_on_applicant(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.notification_channels[EMAIL].send = Mock()
        # after sending, should log event on applicant
        notification.send()
        results = sub.applicant.events.filter(
            name=models.ApplicationEvent.FOLLOWUP_SENT)
        self.assertEqual(results.count(), 1)

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_logs_to_slack_correctly(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.notification_channels[EMAIL].send = Mock()
        notification.send()
        slack.send.assert_called_once_with(
            methods=[EMAIL],
            notification_type='followup',
            submission=sub
            )

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_sends_expected_notification_calls(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        email_followup, sms_followup = Mock(), Mock()
        notification.notification_channels = {
            EMAIL: email_followup,
            SMS: sms_followup
        }
        notification.log_event_to_submission = Mock()
        notification.send()
        self.assertEqual(len(email_followup.send.mock_calls), 1)
        self.assertEqual(len(sms_followup.send.mock_calls), 0)


class TestConfirmationNotification(TestApplicantNotification):

    class_under_test = applicant_notifications.ConfirmationNotification

    def test_builds_correct_context_for_email(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        messages = [org.long_confirmation_message for org in orgs]

        context = notification.get_context(EMAIL)

        self.assertEqual(messages, context['next_steps'])

    def test_builds_correct_context_for_sms(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        messages = [org.short_confirmation_message for org in orgs]

        context = notification.get_context(SMS)

        self.assertEqual(messages, context['next_steps'])

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_logs_two_confirmation_events_on_applicant(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.notification_channels[SMS].send = Mock()
        notification.notification_channels[EMAIL].send = Mock()
        # after sending, should log event on applicant
        notification.send()
        results = sub.applicant.events.filter(
            name=models.ApplicationEvent.CONFIRMATION_SENT)
        self.assertEqual(results.count(), 2)

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_logs_to_slack_correctly(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.notification_channels[SMS].send = Mock()
        notification.notification_channels[EMAIL].send = Mock()
        notification.send()
        slack.send.assert_called_once_with(
            methods=[EMAIL, SMS],
            notification_type='confirmation',
            submission=sub
            )

    @patch(
        'intake.service_objects.applicant_notifications.notifications'
        '.slack_notification_sent')
    def test_sends_expected_notification_calls(self, slack):
        orgs, sub, notification = self.org_notification_and_default_sub()
        email_confirmation, sms_confirmation = Mock(), Mock()
        notification.notification_channels = {
            EMAIL: email_confirmation,
            SMS: sms_confirmation
        }
        notification.log_event_to_submission = Mock()
        notification.send()
        self.assertEqual(len(email_confirmation.send.mock_calls), 1)
        self.assertEqual(len(sms_confirmation.send.mock_calls), 1)
