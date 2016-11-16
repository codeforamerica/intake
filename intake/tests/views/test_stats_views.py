from unittest.mock import patch
from django.test import TestCase
from django.core.urlresolvers import reverse
from intake.tests.base_testcases import IntakeDataTestCase

from intake.tests.mock_serialized_apps import apps as all_apps
from intake.tests.mock_serialized_apps import MOCK_NOW

from intake.views import stats_views
from user_accounts.models import Organization


class TestStats(IntakeDataTestCase):

    private_stats_fields = [
        'referrers',
        'weekly_dropoff_rate',
    ]
    public_stats_fields = [
        'count', 'weekly_total',
        'weekly_mean_completion_time',
        'weekly_median_completion_time'
    ]

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_ebclc',
        'mock_2_submissions_to_sf_pubdef',
        'mock_2_submissions_to_cc_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_application_events'
        ]

    def assert_day_stat_has_correct_fields(self, day, private=False):
        for key in self.private_stats_fields:
            self.assertEqual(private, key in day)
        for key in self.public_stats_fields:
            self.assertIn(key, day)

    def test_contains_data_for_all_orgs(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        stats = response.context['stats']
        org_stats = stats['org_stats']
        org_slugs = list(Organization.objects.filter(
            is_receiving_agency=True
        ).values_list('slug', flat=True))
        org_slugs.append(stats_views.ALL)
        stats_slugs = [data['org']['slug'] for data in org_stats]
        self.assertEqual(set(org_slugs), set(stats_slugs))

    def test_anonymous_user_doesnt_get_json(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        stats = response.context['stats']
        org_stats = stats['org_stats']
        sample_day_stats = org_stats[0]['days'][0]
        self.assert_day_stat_has_correct_fields(sample_day_stats)

    def test_logged_in_user_gets_json(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-stats'))
        response = self.client.get(reverse('intake-stats'))
        stats = response.context['stats']
        org_stats = stats['org_stats']
        sample_day_stats = org_stats[0]['days'][0]
        self.assert_day_stat_has_correct_fields(
            sample_day_stats, private=True)


class TestDailyTotals(TestCase):

    fixtures = [
        'organizations',
        'mock_2_submissions_to_a_pubdef']

    def test_returns_200(self):
        response = self.client.get(reverse('intake-daily_totals'))
        self.assertEqual(response.status_code, 200)


class TestMiscellaneousFunctions(TestCase):

    @patch('intake.views.stats_views.get_todays_date')
    def test_get_aggregate_data_for_org_bucket(self, today):
        today.return_value = MOCK_NOW.date()
        buckets = stats_views.breakup_apps_by_org(all_apps)
        key = 'all'
        result = stats_views.get_aggregate_day_data(buckets[key]['apps'])
        self.assertIn('days', result)
        self.assertIn('total', result)
        self.assertEqual(len(result['days']), 62)
        self.assertEqual(result['total'], 9)

    @patch('intake.views.stats_views.get_todays_date')
    def test_get_day_lookup_structure(self, today):
        today.return_value = MOCK_NOW.date()
        result = stats_views.get_day_lookup_structure()
        self.assertEqual(len(result), 62)

    def test_breakup_apps_by_org(self):
        result = stats_views.breakup_apps_by_org(all_apps)
        counts = {
            key: len(stuff['apps']) for key, stuff in result.items()
        }
        self.assertDictEqual(
            counts,
            {
                'all': 9,
                'cc_pubdef': 3,
                'sf_pubdef': 3,
                'ebclc': 2,
                'a_pubdef': 3
            })
