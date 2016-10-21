from django.test import TestCase
from django.core.urlresolvers import reverse
from intake.tests.base_testcases import IntakeDataTestCase


class TestStats(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_2_submissions_to_cc_pubdef',
        'mock_1_submission_to_multiple_orgs',
        ]

    def test_that_page_shows_counts_by_county(self):
        # get numbers
        all_any = 7
        all_sf = 3
        all_cc = 3
        total = "{} total applications".format(all_any)
        sf_string = "{} applications for San Francisco County".format(all_sf)
        cc_string = "{} applications for Contra Costa County".format(all_cc)
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        for search_term in [total, sf_string, cc_string]:
            self.assertContains(response, search_term)

    def test_anonymous_user_doesnt_get_json(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        self.assertNotIn('applications_json', response.context)

    def test_logged_in_user_gets_json(self):
        self.be_ccpubdef_user()
        response = self.client.get(reverse('intake-stats'))
        self.assertIn('applications_json', response.context)


class TestDailyTotals(TestCase):

    fixtures = [
        'organizations',
        'mock_2_submissions_to_a_pubdef']

    def test_returns_200(self):
        response = self.client.get(reverse('intake-daily_totals'))
        self.assertEqual(response.status_code, 200)
