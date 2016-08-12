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
        command.style.SUCCESS.assert_called_once_with("Successfully referred any unopened apps")


    @patch('intake.management.commands.pull_data_from_typeseam.DataImporter')
    @patch('intake.management.commands.pull_data_from_typeseam.notifications')
    @patch('intake.management.commands.pull_data_from_typeseam.os')
    def test_pull_data_from_typeseam(self, mock_os, notifications, DataImporter):
        command = commands.pull_data_from_typeseam.Command()
        command.stdout = Mock()
        mock_os.environ = {'IMPORT_DATABASE_URL': 'postgres://fake_user:F4k3p455w0rd@dbhost:5432/fake_db_name'}
        command.handle()
        DataImporter.assert_called_once_with(
            import_from=mock_os.environ['IMPORT_DATABASE_URL'],
            ssl=True)
        DataImporter.return_value.import_records.assert_called_once_with(
            delete_existing=True)
        command.stdout.write.assert_called_once_with(
            DataImporter.return_value.report.return_value)
        notifications.slack_simple.send.assert_called_once_with(
            DataImporter.return_value.report.return_value)


    @patch('intake.management.data_import.psycopg2')
    def test_data_importer(self, pg):
        from user_accounts.tests.mock import create_user
        create_user(
            name="Ben Golder",
            email='bgolder@codeforamerica.org',
            username='bengolder')

        from intake.management.data_import import (
            DataImporter,
            USERS_SQL,
            SUBMISSIONS_SQL,
            LOGS_SQL
            )

        importer = DataImporter(
            import_from='postgres://fake_user:F4k3p455w0rd@dbhost:5432/fake_db_name',
            ssl=True
            )

        uuids = mock.uuids(3)

        mock_logs = [
                {'user': 'bgolder'},
                {'user': 'jazmyn'},
                {'user': 'bgolder@codeforamerica.org'},
                {'user': 'jazmyn@codeforamerica.org'},
                {'user': 'someone@agency.org'}]
        for mock_log in mock_logs:
            mock_log.update(
                datetime=mock.fake.date_time_between('-1w', 'now'),
                submission_key=random.choice(uuids),
                event_type=random.choice(['added','referred','opened']))

        mock_db_results = {
            USERS_SQL: [
                {'email': 'bgolder@codeforamerica.org'},
                {'email': 'jazmyn@codeforamerica.org'},
                {'email': 'someone@agency.org'}],
            SUBMISSIONS_SQL: mock.fake_typeseam_submission_dicts(uuids),
            LOGS_SQL: mock_logs
        }
        cursor = MagicMock()
        
        def set_fake_results(sql):
            data = mock_db_results[sql]
            cursor.__iter__.return_value = data

        cursor.execute.side_effect = set_fake_results

        importer._cursor = cursor
        importer.import_records(delete_existing=True)

        expected_report = '''Beginning data import  from `fake_db_name` on `dbhost`
--------
Successfully imported 3 users:
\tfound bgolder@codeforamerica.org
\tcreated jazmyn@codeforamerica.org
\tcreated someone@agency.org
--------
No FormSubmission instances exist. Not deleting anything.
--------
Successfully imported 3 form submissions from `fake_db_name` on `dbhost`
--------
No ApplicationLogEntry instances exist. Not deleting anything.
--------
Successfully imported 5 event logs from `fake_db_name` on `dbhost`'''
        self.assertEqual(importer.report(), expected_report)

    def test_load_initial_data(self):
        mock_stdout = Mock()
        existing_counties = models.County.objects.all()
        self.assertEqual(len(existing_counties), 3)
        from intake.management.commands import load_initial_data
        cmd = load_initial_data.Command()
        cmd.stdout = mock_stdout
        cmd.handle()
        existing_counties = models.County.objects.all()
        self.assertEqual(len(existing_counties), 3)
        num_calls = len(mock_stdout.write.call_args_list)
        self.assertTrue(num_calls > 3 + 2)
