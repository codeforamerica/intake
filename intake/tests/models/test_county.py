from django.test import TestCase
from user_accounts import models as auth_models
from intake import models
from intake.tests import factories
from user_accounts.tests.factories import FakeOrganizationFactory
from formation import field_types


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
        answers = {}
        for county_slug, agency_name in expected_matches:
            county = counties.filter(slug=county_slug).first()
            organization = county.get_receiving_agency(answers)
            self.assertEqual(organization.name, agency_name)

    def test_get_receiving_agency_alameda_eligible_for_apd(self):
        alameda = models.County.objects.get(slug='alameda')
        eligible_for_apd = dict(monthly_income=2999, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(eligible_for_apd)
        alameda_pubdef = auth_models.Organization.objects.get(slug='a_pubdef')
        self.assertEqual(result, alameda_pubdef)

    def test_get_receiving_agency_high_income_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug='alameda')
        ebclc_high_income = dict(monthly_income=3000, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(ebclc_high_income)
        ebclc = auth_models.Organization.objects.get(slug='ebclc')
        self.assertEqual(result, ebclc)

    def test_get_receiving_agency_owns_home_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug='alameda')
        ebclc_owns_home = dict(monthly_income=2999, owns_home=field_types.YES)
        result = alameda.get_receiving_agency(ebclc_owns_home)
        ebclc = auth_models.Organization.objects.get(slug='ebclc')
        self.assertEqual(result, ebclc)


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
        results = list(models.County.objects.get_county_choices_query())
        self.assertIn(live_org.county, results)
        self.assertIn(live_org.county, results)
        self.assertNotIn(not_listed, results)

    def test_get_county_choices_query_live(self):
        live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=True)
        not_live_org = FakeOrganizationFactory(
            county=factories.CountyFactory(), is_live=False)
        not_listed = models.County.objects.get(slug='not_listed')
        with self.settings(LIVE_COUNTY_CHOICES=True):
            results = list(models.County.objects.get_county_choices_query())
        self.assertIn(live_org.county, results)
        self.assertNotIn(not_live_org.county, results)
        self.assertNotIn(not_listed, results)
