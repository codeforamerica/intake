from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
import pandas
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
        cfa_app = intake_factories.make_apps_for('cfa', count=1)
        ebclc_app = intake_factories.make_apps_for('ebclc', count=1)
        both_app = intake_factories.make_apps_for('cfa', 'ebclc', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        df = pandas.read_excel(response)
        import ipdb; ipdb.set_trace()

    def test_org_user_gets_apps_from_own_org_only(self):
        pass

    def test_org_user_w_no_apps_gets_empty_excel_spreadseet(self):
        pass
