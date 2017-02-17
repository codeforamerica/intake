from django.test import TestCase
from intake.services import statistics
from user_accounts.models import Organization
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES


class TestGetStatusUpdateSuccessMetrics(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_returns_expected_data(self):
        number_of_orgs = Organization.objects.filter(
            is_receiving_agency=True).count()
        with self.assertNumQueries(4):
            data = statistics.get_status_update_success_metrics()
        data_dict = dict(data)
        self.assertEqual(len(data), number_of_orgs + 1)
        self.assertIn(
            statistics.ALL[1], data_dict)
        for org_name, counts in data:
            self.assertIn(
                statistics.TOTAL,
                dict(counts))
