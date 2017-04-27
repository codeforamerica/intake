from unittest.mock import patch, Mock
from intake.tests.base_testcases import ExternalNotificationsPatchTestCase
from intake.tests import mock, factories
from intake.tests.mock_org_answers import get_answers_for_orgs
from intake.management.commands import send_followups
from intake.models import Applicant
from user_accounts.models import Organization


class TestCommand(ExternalNotificationsPatchTestCase):

    fixtures = [
        'counties', 'organizations']

    @patch('intake.management.commands.send_followups.is_the_weekend')
    @patch('intake.management.commands.send_followups.FollowupsService')
    def test_doesnt_do_anything_on_the_weekend(
            self, FollowupsService, is_the_weekend):
        is_the_weekend.return_value = True
        command = send_followups.Command()
        command.stdout = Mock()
        command.handle()
        FollowupsService.assert_not_called()

    @patch('intake.management.commands.send_followups.is_the_weekend')
    @patch('intake.notifications.slack_simple.send')
    def test_expected_weekday_run(self, slack, is_the_weekend):
        is_the_weekend.return_value = False
        org = Organization.objects.get(slug='ebclc')
        dates = sorted([mock.get_old_date() for i in range(464, 469)])
        for date, pk in zip(dates, range(464, 469)):
            factories.FormSubmissionWithOrgsFactory.create(
                id=pk,
                date_received=date,
                organizations=[org],
                answers=get_answers_for_orgs(
                    [org],
                    contact_preferences=[
                        'prefers_email',
                        'prefers_sms'],
                    phone='4445551111',
                    email='test@test.com',
                ))
        command = send_followups.Command()
        command.stdout = Mock()
        command.handle()
        self.assertEqual(
            len(slack.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.email_followup.send.mock_calls), 4)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 4)
