from django.urls import reverse
from intake.tests.base_testcases import (
    IntakeDataTestCase, ALL_APPLICATION_FIXTURES)

from intake import models
from intake.tests.factories import FormSubmissionWithOrgsFactory
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

    def test_contains_data_for_all_live_orgs(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        stats = response.context_data['stats']
        org_stats = stats['org_stats']
        org_slugs = list(Organization.objects.filter(
            is_receiving_agency=True,
            is_live=True
        ).values_list('slug', flat=True))
        org_slugs.append('all')
        stats_slugs = [data['org']['slug'] for data in org_stats]
        self.assertEqual(set(org_slugs), set(stats_slugs))

    def test_doesnt_contain_data_for_nonlive_orgs(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-stats'))
        stats = response.context_data['stats']
        org_stats = stats['org_stats']
        org_slugs = list(Organization.objects.filter(
            is_receiving_agency=True,
            is_live=False
        ).values_list('slug', flat=True))
        stats_slugs = [data['org']['slug'] for data in org_stats]
        self.assertFalse = set(org_slugs) and set(stats_slugs)

    def test_nonlive_application_doesnt_break_stats_page(self):
        self.be_monitor_user()
        non_live_org = Organization(
            name="Maquis",
            slug="maquis",
            is_receiving_agency=True,
            is_live=False,
            county=models.County.objects.first()
        )
        non_live_org.save()
        FormSubmissionWithOrgsFactory.create(
            organizations=[non_live_org], answers={})
        response = self.client.get(reverse('intake-stats'))
        self.assertEqual(response.status_code, 200)
