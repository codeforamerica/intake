from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape as html_escape
from intake.views import followup_views
from intake.tests.services.test_followups import get_old_date
from intake.tests import mock


class TestFollowupIndex(AuthIntegrationTestCase):
    fixtures = [
        'counties', 'organizations',
        'mock_profiles'
    ]

    def test_with_no_apps(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-followups'))
        self.assertContains(
            response,
            html_escape(
                followup_views.FollowupsIndex.empty_set_message))

    def test_with_a_few_apps(self):
        subs = [
            mock.FormSubmissionFactory.create(
                date_received=get_old_date())
            for i in range(3)
        ]
        self.be_cfa_user()
        response = self.client.get(reverse('intake-followups'))
        for sub in subs:
            self.assertContains(
                response,
                html_escape(sub.get_absolute_url()))

    def test_staff_users_only(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-followups'))
        self.assertEqual(response.status_code, 200)
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-followups'))
        self.assertEqual(response.status_code, 302)
        self.be_anonymous()
        response = self.client.get(reverse('intake-followups'))
        self.assertEqual(response.status_code, 302)
