from django.test import TestCase
from django.core.urlresolvers import reverse
from intake.tests.base_testcases import (
    IntakeDataTestCase, ALL_APPLICATION_FIXTURES)

from intake.tests.mock_serialized_apps import apps as all_apps

from intake.views import stats_views
from intake import constants
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

    fixtures = ALL_APPLICATION_FIXTURES

    def assert_day_stat_has_correct_fields(self, day, private=False):
        for key in self.private_stats_fields:
            self.assertEqual(private, key in day)
        for key in self.public_stats_fields:
            self.assertIn(key, day)

    def test_contains_data_for_all_orgs(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        stats = response.context_data['stats']
        org_stats = stats['org_stats']
        org_slugs = list(Organization.objects.filter(
            is_receiving_agency=True
        ).values_list('slug', flat=True))
        org_slugs.append(constants.Organizations.ALL)
        stats_slugs = [data['org']['slug'] for data in org_stats]
        self.assertEqual(set(org_slugs), set(stats_slugs))

    def test_anonymous_user_doesnt_see_private_aggs(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        for private_agg in ('error rate', 'dropoff rate', 'Channel'):
            self.assertNotContains(response, private_agg)

    def test_user_in_performance_monitor_group_sees_error_and_dropoff(self):
        self.be_monitor_user()
        response = self.client.get(reverse('intake-stats'))
        self.assertContains(response, 'error rate')
        self.assertContains(response, 'dropoff rate')

    def test_user_in_application_reviewer_group_sees_error_and_dropoff(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-stats'))
        self.assertContains(response, 'error rate')
        self.assertContains(response, 'dropoff rate')


class TestMiscellaneousFunctions(TestCase):

    def test_breakup_apps_by_org(self):
        result = stats_views.breakup_apps_by_org(all_apps)
        counts = {
            org_agg['org']['slug']: len(org_agg['apps']) for org_agg in result
        }
        self.assertDictEqual(
            counts,
            {
                'all': 9,
                'cc_pubdef': 3,
                'sf_pubdef': 3,
                'ebclc': 2,
                'a_pubdef': 3,
            })
