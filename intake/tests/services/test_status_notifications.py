from unittest.mock import Mock, patch
from intake.tests.mock import FormSubmissionFactory
from intake.tests.mock_utils import SimpleMock
from django.test import TestCase
from intake import services, models
from user_accounts.models import Organization


class TestSendAndSaveNewStatus(TestCase):

    fixtures = [
        'counties', 'organizations',
        'template_options', 'mock_profiles']

    @patch('intake.services.status_notifications.notifications')
    @patch('intake.services.status_notifications.messages')
    def test_messages_both_contain_intro(self, messages, notifications):
        # given:
        #   - status update data
        #       - application
        #           - organization
        #           - submission
        #   - notification data
        # assert:
        #   - base and sent messages both have intro message
        mock_request = Mock()
        org = Organization.objects.filter(is_live=True).last()
        profile = org.profiles.first()
        submission = FormSubmissionFactory(organizations=[org])
        application = submission.applications.first()
        status_update_data = dict(
            author=profile.user,
            application=application,
            status_type=models.StatusType.objects.first(),
            next_steps=[],
            additional_information="")
        notification_data = dict(
            sent_message="hey there")

        services.status_notifications.send_and_save_new_status(
            mock_request, notification_data, status_update_data)

        expected_intro_message = \
            services.status_notifications.get_notification_intro(profile)
        latest_update = models.StatusUpdate.objects.filter(
            application=application).latest('updated')
        notification = latest_update.notification
        self.assertIn(expected_intro_message, notification.base_message)
        self.assertIn(expected_intro_message, notification.sent_message)
        args = notifications.send_simple_front_notification.call_args[0]
        self.assertIn(expected_intro_message, args[1])


class TestGetBaseMessageFromStatusUpdateData(TestCase):

    fixtures = [
        'counties', 'organizations',
        'template_options', 'mock_profiles']

    def test_no_next_step_intro_if_no_next_steps(self):
        mock_request = Mock()
        org = Organization.objects.filter(is_live=True).last()
        profile = org.profiles.first()
        submission = FormSubmissionFactory(organizations=[org])
        application = submission.applications.first()
        status_update_data = dict(
            author=profile.user,
            application=application,
            status_type=models.StatusType.objects.first(),
            next_steps=[],
            additional_information="")
        result = services.status_notifications\
            .get_base_message_from_status_update_data(
                mock_request, status_update_data
            )
        next_step_intro = 'Here are your next steps:'
        self.assertNotIn(next_step_intro, result)

    def test_next_step_intro_if_next_steps(self):
        mock_request = Mock()
        org = Organization.objects.filter(is_live=True).last()
        profile = org.profiles.first()
        submission = FormSubmissionFactory(organizations=[org])
        application = submission.applications.first()
        status_update_data = dict(
            author=profile.user,
            application=application,
            status_type=models.StatusType.objects.first(),
            next_steps=[models.NextStep.objects.first()],
            additional_information="")
        result = services.status_notifications\
            .get_base_message_from_status_update_data(
                mock_request, status_update_data
            )
        next_step_intro = 'Here are your next steps:'
        self.assertIn(next_step_intro, result)
