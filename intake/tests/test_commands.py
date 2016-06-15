import os as true_os
from unittest.mock import Mock, patch, MagicMock
from intake.tests import mock
from django.test import TestCase

from intake.management import commands

class TestCommands(TestCase):

    @patch('intake.management.commands.send_unopened_apps_notification.models')
    def test_send_unopened_apps_notification_(self, models):
        command = Mock()
        commands.send_unopened_apps_notification.Command.handle(command)
        models.FormSubmission.refer_unopened_apps.assert_called_once_with()
        command.style.SUCCESS.assert_called_once_with(
            models.FormSubmission.refer_unopened_apps.return_value)


    def test_data_importer(self):
        from user_accounts.tests.mock import create_user
        create_user(
            name="Ben Golder",
            email='bgolder@codeforamerica.org',
            username='bengolder')
        from intake.management.data_import import DataImporter
        importer = DataImporter(
            import_from=true_os.environ.get('IMPORT_DATABASE_URL', '')
            )
        importer.import_records(delete_existing=True)
        print('\n\n' + importer.report())
