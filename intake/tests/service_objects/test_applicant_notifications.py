from unittest.mock import patch, Mock
from user_accounts.models import Organization
from intake.constants import Organizations
from intake.tests import factories
from intake.tests.mock_org_answers import get_answers_for_orgs
from intake.tests.base_testcases import ExternalNotificationsPatchTestCase
from intake.tests.services.test_followups import get_old_date
from intake.service_objects import applicant_notifications
from intake.constants import SMS, EMAIL
from intake import utils, models


class TestApplicantNotification(ExternalNotificationsPatchTestCase):

    fixtures = [
        'counties',
        'organizations'
    ]

    class_under_test = applicant_notifications.ApplicantNotification

    def many_orgs(self):
        orgs = list(Organization.objects.filter(
                    slug__in=[
                        Organizations.SF_PUBDEF,
                        Organizations.EBCLC]))
        orgs = utils.sort_orgs_in_default_order(orgs)
        return orgs

    def make_full_submission(self, orgs, **answer_overrides):
        answers = get_answers_for_orgs(
            orgs,
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
        return factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(),
            anonymous_name="Cerulean Beetle",
            organizations=orgs,
            answers=answers
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

    def test_logs_one_followup_event_on_applicant(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        # after sending, should log event on applicant
        notification.send()
        results = sub.applicant.events.filter(
            name=models.ApplicationEvent.FOLLOWUP_SENT)
        self.assertEqual(results.count(), 1)

    def test_logs_to_slack_correctly(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.send()
        self.notifications.slack_notification_sent.send.\
            assert_called_once_with(
                methods=[EMAIL],
                notification_type='followup',
                submission=sub
            )

    def test_sends_expected_notification_calls(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.log_event_to_submission = Mock()
        notification.send()
        self.assertEqual(
            len(self.notifications.email_followup.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_followup.send.mock_calls), 0)


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

    def test_logs_two_confirmation_events_on_applicant(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        # after sending, should log event on applicant
        notification.send()
        results = sub.applicant.events.filter(
            name=models.ApplicationEvent.CONFIRMATION_SENT)
        self.assertEqual(results.count(), 2)

    def test_logs_to_slack_correctly(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.send()
        self.notifications.slack_notification_sent.send\
            .assert_called_once_with(
                methods=[EMAIL, SMS],
                notification_type='confirmation',
                submission=sub
            )

    def test_logs_to_slack_correctly_with_one_preference(self):
        orgs, sub, notification = self.org_notification_and_default_sub(
            contact_preferences=['prefers_email'])
        notification.send()
        self.notifications.slack_notification_sent.send\
            .assert_called_once_with(
                methods=[EMAIL],
                notification_type='confirmation',
                submission=sub
            )

    def test_sends_expected_notification_calls(self):
        orgs, sub, notification = self.org_notification_and_default_sub()
        notification.log_event_to_submission = Mock()
        notification.send()
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 1)
