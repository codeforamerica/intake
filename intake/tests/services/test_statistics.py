from django.test import TestCase
from intake.services import statistics
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES


class TestGetOrgDataDict(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_returns_expected_data(self):
        results = statistics.get_org_data_dict()
        all_orgs = results.pop(0)
        dates = [week['date'] for week in all_orgs['weekly_totals']]
        for org_data in results:
            self.assertIn('total', org_data)
            self.assertIn('apps_this_week', org_data)
            self.assertIn('org', org_data)
            self.assertListEqual(
                dates, [week['date'] for week in org_data['weekly_totals']])
