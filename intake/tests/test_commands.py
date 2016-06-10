from unittest.mock import Mock, patch, MagicMock
from intake.tests import mock
from django.test import TestCase

from intake.management import commands

class TestCommands(TestCase):

    @patch('intake.management.commands.send_unopened_apps_notification.notifications')
    @patch('intake.management.commands.send_unopened_apps_notification.models')
    @patch('intake.management.commands.send_unopened_apps_notification.settings')
    def test_send_unopened_apps_notification_with_no_apps(self, settings, models, notifications):
        settings.DEFAULT_NOTIFICATION_EMAIL = "someone@agency.org"

        command = commands.send_unopened_apps_notification.Command()
        command.report_success = Mock()
        
        # case: no unopened apps
        models.FormSubmission.get_unopened_apps.return_value = []

        command.handle()
        notifications.front_email_daily_app_bundle.send.assert_not_called()
        command.report_success.assert_called_once_with(
            "No unopened applications. Didn't email someone@agency.org")

        # case: some unopened apps
        command.report_success.reset_mock()
        models.FormSubmission.get_unopened_apps.return_value = [
            Mock(id=1), Mock(id=2)
            ]
        
        command.handle()
        notifications.front_email_daily_app_bundle.send.assert_called_once_with(
            to="someone@agency.org",
            count=2,
            submission_ids=[1,2])
        command.report_success.assert_called_once_with(
            "Emailed someone@agency.org with a link to 2 unopened applications")


    @patch('intake.management.commands.send_unopened_apps_notification.settings')
    def test_report_success(self, settings):
        command = commands.send_unopened_apps_notification.Command()

        command.stdout = Mock()
        command.style = Mock()

        command.report_success("Hello")
        command.style.SUCCESS.assert_called_once_with("Hello")
        command.stdout.write.assert_called_once_with(
            command.style.SUCCESS.return_value)


