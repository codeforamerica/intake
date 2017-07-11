from unittest.mock import Mock, patch
from django.test import TestCase
from intake.management import commands


class TestCommands(TestCase):

    @patch(
        'intake.management.commands.send_unopened_apps_notification'
        '.BundlesService')
    def test_send_unopened_apps_notification(self, BundlesService):
        command = Mock()
        commands.send_unopened_apps_notification.Command.handle(command)
        BundlesService.count_unreads_and_send_notifications_to_orgs\
            .assert_called_once_with()
        command.style.SUCCESS.assert_called_once_with(
            "Successfully referred any unopened apps")
