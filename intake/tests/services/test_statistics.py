import datetime
from django.test import TestCase
from intake.constants import PACIFIC_TIME
from intake.services import statistics
from intake import utils
from intake.tests.factories import FormSubmissionWithOrgsFactory
from user_accounts.models import Organization
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


class TestRollupSubs(TestCase):

    def test_diff_dates_same_sub_no_change(self):
        # make sure that if the application times differ slightly, it does
        # not affect the count
        one_org = Organization(name="House Stark", slug='stark')
        one_org.save()
        other_org = Organization(name="House Tyrell", slug='tyrell')
        other_org.save()
        sub = FormSubmissionWithOrgsFactory(
            organizations=[one_org, other_org],
            answers={})
        app = sub.applications.first()
        app.created = app.created + datetime.timedelta(milliseconds=1)
        app.save()
        results = statistics.rollup_subs(
            statistics.get_app_dates_sub_ids_org_ids())
        self.assertEqual(len(results), 1)


class TestMakeYearWeeks(TestCase):

    def test_expected_week(self):
        # 19th week of 2017
        same_week = [
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=14)),  # sunday
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=12)),  # friday
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=11)),  # friday
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=8)),   # monday
        ]
        # 20th week of 2017
        next_week = [
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=15)),  # monday
            PACIFIC_TIME.localize(
                datetime.datetime(year=2017, month=5, day=21)),  # sunday
        ]
        for date in same_week:
            result = statistics.as_year_week(date)
            self.assertEqual(result, '2017-19-1')
        for date in next_week:
            result = statistics.as_year_week(date)
            self.assertEqual(result, '2017-20-1')

    def test_year_week_conversion(self):
        result = statistics.from_year_week('2017-19-1')
        expected_dt = '2017-05-08'
        self.assertEqual(expected_dt, result.strftime('%Y-%m-%d'))
        result = statistics.from_year_week('2017-20-1')
        expected_dt = '2017-05-15'
        self.assertEqual(expected_dt, result.strftime('%Y-%m-%d'))

    def test_make_year_weeks_output(self):
        todays_date = utils.get_todays_date()
        next_week = todays_date + datetime.timedelta(days=7)
        last_year_week = statistics.as_year_week(todays_date)
        too_far_year_week = statistics.as_year_week(next_week)
        year_weeks = statistics.make_year_weeks()
        expected_last_yw, last_date, last_date_from_yw = year_weeks[-1]
        self.assertNotEqual(too_far_year_week, expected_last_yw)
        self.assertEqual(last_year_week, expected_last_yw)
