import logging
from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase
from project.services import query_params
from project.tests.utils import login
from project.tests.assertions import assertInLogsCount
from intake.tests import factories as intake_factories
from user_accounts.tests import factories as user_accounts_factories


class TestCasePrintoutPDFView(TestCase):
    fixtures = ['groups']

    def test_anonymous_users_redirected_to_login(self):
        sub = intake_factories.make_apps_for(
            'a_pubdef', count=1)[0].form_submission
        response = self.client.get(
            reverse(
                'intake-case_printout', kwargs=dict(submission_id=sub.id)))
        self.assertIn(reverse('user_accounts-login'), response.url)
        self.assertEqual(response.status_code, 302)

    def test_users_from_wrong_org_redirected_to_profile(self):
        profile = user_accounts_factories.app_reviewer('cc_pubdef')
        login(self.client, profile)
        sub = intake_factories.make_apps_for(
            'a_pubdef', count=1)[0].form_submission
        response = self.client.get(
            reverse(
                'intake-case_printout', kwargs=dict(submission_id=sub.id)))
        self.assertRedirects(response, reverse('user_accounts-profile'))

    def test_marks_apps_as_opened(self):
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        login(self.client, profile)
        submission = intake_factories.make_apps_for(
                    'a_pubdef', count=1)[0].form_submission
        self.client.get(
            reverse(
                'intake-case_printout', kwargs=dict(
                    submission_id=submission.id)))
        application = submission.applications.filter(
            organization=profile.organization).first()
        self.assertTrue(application.has_been_opened)

    def test_fires_expected_mixpanel_events(self):
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        login(self.client, profile)
        submission = intake_factories.make_apps_for(
                    'a_pubdef', count=1)[0].form_submission
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.get(
                reverse('intake-case_printout', kwargs=dict(
                        submission_id=submission.id)))
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})

    def test_cfa_staff_can_view(self):
        profile = user_accounts_factories.followup_user()
        login(self.client, profile)
        submission = intake_factories.make_apps_for(
                    'a_pubdef', count=1)[0].form_submission
        response = self.client.get(
                reverse('intake-case_printout', kwargs=dict(
                        submission_id=submission.id)))
        self.assertEqual(response.status_code, 200)


class TestPrintoutForApplicationsView(TestCase):
    view_name = 'intake-pdf_printout_for_apps'
    fixtures = ['groups']

    @patch('project.alerts.send_email_to_admins')
    def test_if_invalid_ids(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('cc_pubdef')
        profile = user_accounts_factories.app_reviewer('cc_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids + [918274]))
        self.assertEqual(200, response.status_code)
        email_alert.assert_not_called()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, "{}?next={}".format(
            reverse('user_accounts-login'), reverse(self.view_name)))

    @patch('project.alerts.send_email_to_admins')
    def test_org_user_from_wrong_org_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('cc_pubdef')
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    def test_org_user_from_correct_org_can_access(self):
        app_ids = intake_factories.make_app_ids_for('cc_pubdef')
        profile = user_accounts_factories.app_reviewer('cc_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    def test_followup_user_can_access(self):
        app_ids = intake_factories.make_app_ids_for('cc_pubdef')
        profile = user_accounts_factories.followup_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    @patch('project.alerts.send_email_to_admins')
    def test_monitor_user_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('cc_pubdef')
        profile = user_accounts_factories.monitor_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)
