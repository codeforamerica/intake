import logging
from unittest.mock import patch

from django.urls import reverse
from django.test import TestCase

from project.services import query_params
from project.tests.utils import login
from intake import models
from intake.tests import factories as intake_factories
from user_accounts.tests import factories as user_accounts_factories
from project.tests.assertions import assertInLogsCount


def prebuilt_pdf_for_ids(app_ids):
    prebuilt = intake_factories.PrebuiltPDFBundleFactory()
    prebuilt.applications.add(*app_ids)
    return prebuilt


class TestPrebuiltPDFBundleWrapperView(TestCase):
    view_name = 'intake-pdf_bundle_wrapper_view'
    fixtures = ['groups']

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, "{}?next={}".format(
            reverse('user_accounts-login'), reverse(self.view_name)))

    @patch('project.alerts.send_email_to_admins')
    def test_org_user_from_wrong_org_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    def test_org_user_from_correct_org_can_access(self):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    def test_followup_user_can_access(self):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.followup_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    @patch('project.alerts.send_email_to_admins')
    def test_monitor_user_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.monitor_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    def test_org_user_who_needs_prebuilt_sees_prebuilt_link(self):
        intake_factories.FillablePDFFactory()
        prebuilt = intake_factories.PrebuiltPDFBundleFactory()
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        prebuilt.applications.add(*app_ids)
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertContains(response, prebuilt.get_absolute_url())

    def test_org_user_who_doesnt_need_prebuilt_gets_printout(self):
        app_ids = intake_factories.make_app_ids_for('a_pubdef')
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        printout_url = query_params.get_url_for_ids(
            'intake-pdf_printout_for_apps', app_ids)
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertContains(response, printout_url)

    @patch('project.alerts.send_email_to_admins')
    def test_invalid_query_params_returns_not_allowed(self, email_alert):
        prebuilt = intake_factories.PrebuiltPDFBundleFactory()
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        prebuilt.applications.add(*app_ids)
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids + ['omg']))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    def test_marks_apps_as_opened(self):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        all_apps_opened = all(models.Application.objects.filter(
            id__in=app_ids).values_list('has_been_opened', flat=True))
        self.assertTrue(all_apps_opened)

    def test_shows_flash_message(self):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef', count=3)
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertContains(response, str(
            '3 applications have been marked as “Read” and moved to the '
            '“Needs Status Update” folder'))

    def test_fires_expected_mixpanel_events(self):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.client.get(
                query_params.get_url_for_ids(self.view_name, app_ids))
        assertInLogsCount(logs, {'event_name=app_opened': len(app_ids)})
        assertInLogsCount(logs, {'event_name=user_app_opened': len(app_ids)})


class TestPrebuiltPDFBundleFileView(TestCase):
    view_name = 'intake-pdf_bundle_file_view'
    fixtures = ['groups']

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, "{}?next={}".format(
            reverse('user_accounts-login'), reverse(self.view_name)))

    @patch('project.alerts.send_email_to_admins')
    def test_org_user_from_wrong_org_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.app_reviewer('a_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    @patch(
        'intake.services.pdf_service.get_prebuilt_pdf_bundle_for_app_id_set')
    def test_org_user_from_correct_org_can_access(self, get_bundle):
        get_bundle.return_value.pdf = b'bytez'
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        prebuilt_pdf_for_ids(app_ids)
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    @patch(
        'intake.services.pdf_service.get_prebuilt_pdf_bundle_for_app_id_set')
    def test_followup_user_can_access(self, get_bundle):
        get_bundle.return_value.pdf = b'bytez'
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        prebuilt_pdf_for_ids(app_ids)
        profile = user_accounts_factories.followup_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertEqual(200, response.status_code)

    @patch('project.alerts.send_email_to_admins')
    def test_monitor_user_gets_not_allowed(self, email_alert):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        profile = user_accounts_factories.monitor_user()
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids))
        self.assertRedirects(response, reverse('user_accounts-profile'))
        self.assertEqual(1, email_alert.call_count)

    @patch(
        'intake.services.pdf_service.get_prebuilt_pdf_bundle_for_app_id_set')
    @patch('project.alerts.send_email_to_admins')
    def test_ignores_invalid_ids(self, email_alert, get_bundle):
        app_ids = intake_factories.make_app_ids_for('sf_pubdef')
        prebuilt_pdf_for_ids(app_ids)
        get_bundle.return_value.pdf = b'bytez'
        profile = user_accounts_factories.app_reviewer('sf_pubdef')
        login(self.client, profile)
        response = self.client.get(
            query_params.get_url_for_ids(self.view_name, app_ids + [918274]))
        self.assertEqual(200, response.status_code)
        email_alert.assert_not_called()
