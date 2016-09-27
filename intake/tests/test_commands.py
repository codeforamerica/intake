import random
from unittest.mock import Mock, patch, MagicMock
from intake.tests import mock
from django.test import TestCase

from intake.management import commands
from intake import models


class TestCommands(TestCase):

    @patch('intake.management.commands.send_unopened_apps_notification.submission_bundler')
    def test_send_unopened_apps_notification(self, submission_bundler):
        command = Mock()
        commands.send_unopened_apps_notification.Command.handle(command)
        submission_bundler.bundle_and_notify.assert_called_once_with()
        command.style.SUCCESS.assert_called_once_with(
            "Successfully referred any unopened apps")
