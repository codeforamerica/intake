import io
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
import pandas
import xlrd
from intake.tests import factories as intake_factories
from user_accounts.tests import factories as accounts_factories
from user_accounts.models import Organization


class TestExcelDownloadView(TestCase):
    view_name = 'intake-excel_download'
    fixtures = ['groups', 'counties', 'organizations']

    def test_anon_is_redirected_to_login(self):
        response = self.client.get(reverse(self.view_name))
        self.assertIn(reverse('user_accounts-login'), response.url)
        self.assertEqual(response.status_code, 302)

    def test_followup_staff_gets_not_listed_apps(self):
        user = accounts_factories.followup_user().user
        cfa_apps = intake_factories.make_apps_for('cfa', count=1)
        ebclc_apps = intake_factories.make_apps_for('ebclc', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        df = pandas.read_excel(io.BytesIO(response.content))
        for app in cfa_apps:
            with self.subTest(app=app):
                self.assertTrue(any(df.id == app.id))
        for app in ebclc_apps:
            with self.subTest(app=app):
                self.assertFalse(any(df.id == app.id))

    def test_org_user_gets_apps_from_own_org_only(self):
        user = accounts_factories.app_reviewer('ebclc').user
        cc_apps = intake_factories.make_apps_for('cc_pubdef', count=1)
        ebclc_apps = intake_factories.make_apps_for('ebclc', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        df = pandas.read_excel(io.BytesIO(response.content))
        for app in cc_apps:
            with self.subTest(app=app):
                self.assertFalse(any(df.id == app.id))
        for app in ebclc_apps:
            with self.subTest(app=app):
                self.assertTrue(any(df.id == app.id))

    def test_org_user_w_no_apps_gets_empty_excel_spreadseet(self):
        user = accounts_factories.app_reviewer('ebclc').user
        cfa_apps = intake_factories.make_apps_for('cc_pubdef', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        df = pandas.read_excel(io.BytesIO(response.content))
        self.assertEqual(0, len(df))
