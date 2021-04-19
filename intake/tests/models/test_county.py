from django.test import TestCase
from intake import models
from intake.tests import factories
from user_accounts.tests.factories import FakeOrganizationFactory


class TestCounty(TestCase):

    fixtures = ['counties', 'organizations']

    def test_county_init(self):
        county = models.County(slug="yolo", description="Yolo County")
        self.assertEqual(county.slug, "yolo")
        self.assertEqual(county.description, "Yolo County")

    def test_get_receiving_agency_with_no_criteria(self):
        expected_matches = (
            ('sanfrancisco', "San Francisco Public Defender"),
            ('contracosta', "Contra Costa Public Defender"))
        counties = models.County.objects.all()
        for county_slug, agency_name in expected_matches:
            county = counties.filter(slug=county_slug).first()
            organization = county.get_receiving_agency()
            self.assertEqual(organization.name, agency_name)

    def test_get_visible_organizations_returns_only_live_orgs_when_only_show_live_counties_is_true(self):
        county = factories.CountyFactory()
        live_org = FakeOrganizationFactory(county=county, is_live=True)
        not_live_org = FakeOrganizationFactory(county=county, is_live=False)

        with self.settings(ONLY_SHOW_LIVE_COUNTIES=True):
            results = county.get_visible_organizations()
            self.assertIn(live_org, results)
            self.assertNotIn(not_live_org, results)

    def test_get_visible_organizations_returns_only_live_orgs_when_only_show_live_counties_is_false(self):
        county = factories.CountyFactory()
        other_county = factories.CountyFactory()
        live_org = FakeOrganizationFactory(county=county, is_live=True)
        not_live_org = FakeOrganizationFactory(county=county, is_live=False)
        random_org = FakeOrganizationFactory(county=other_county, is_live=False)

        with self.settings(ONLY_SHOW_LIVE_COUNTIES=False):
            results = county.get_visible_organizations()
            self.assertIn(live_org, results)
            self.assertIn(not_live_org, results)
            self.assertNotIn(random_org, results)


class TestCountyManager(TestCase):

    fixtures = ['counties']

    def test_annotate_is_not_listed(self):
        qset = models.County.objects.annotate_is_not_listed()
        not_listed = qset.filter(slug='not_listed').first()
        self.assertTrue(not_listed)
        for row in qset:
            with self.subTest(row=row):
                self.assertTrue(hasattr(row, 'is_not_listed'))
                if row.slug == 'not_listed':
                    self.assertTrue(row.is_not_listed)
                else:
                    self.assertFalse(row.is_not_listed)

    def test_order_by_name_or_not_listed(self):
        counties = list(models.County.objects.order_by_name_or_not_listed())
        count = len(counties)
        last_county = counties[count - 1]
        self.assertEqual(last_county.slug, 'not_listed')
        for county in counties:
            if county != last_county:
                with self.subTest(county=county):
                    self.assertFalse(county.slug == 'not_listed')

    def test_get_county_choices_query_default(self):
        live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=True)
        not_live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=False)
        not_listed = models.County.objects.get(slug='not_listed')
        with self.settings(ONLY_SHOW_LIVE_COUNTIES=False):
            results = list(models.County.objects.get_county_choices_query())
        self.assertIn(live_org.county, results)
        self.assertIn(not_live_org.county, results)
        self.assertNotIn(not_listed, results)

    def test_get_county_choices_query_live(self):
        live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=True)
        not_live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=False)
        not_listed = models.County.objects.get(slug='not_listed')
        with self.settings(ONLY_SHOW_LIVE_COUNTIES=True):
            results = list(models.County.objects.get_county_choices_query())
        self.assertIn(live_org.county, results)
        self.assertNotIn(not_live_org.county, results)
        self.assertNotIn(not_listed, results)
