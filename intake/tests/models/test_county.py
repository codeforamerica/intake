from django.test import TestCase

from user_accounts import models as auth_models
from intake import models, constants
from formation import field_types


class TestCounty(TestCase):

    fixtures = ['counties', 'organizations']

    def test_county_init(self):
        county = models.County(slug="yolo", description="Yolo County")
        self.assertEqual(county.slug, "yolo")
        self.assertEqual(county.description, "Yolo County")

    def test_get_receiving_agency_with_no_criteria(self):
        expected_matches = (
            (constants.Counties.SAN_FRANCISCO,
                "San Francisco Public Defender"),
            (constants.Counties.CONTRA_COSTA, "Contra Costa Public Defender"))
        counties = models.County.objects.all()
        answers = {}
        for county_slug, agency_name in expected_matches:
            county = counties.filter(slug=county_slug).first()
            organization = county.get_receiving_agency(answers)
            self.assertEqual(organization.name, agency_name)

    def test_get_receiving_agency_alameda_eligible_for_apd(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        eligible_for_apd = dict(monthly_income=2999, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(eligible_for_apd)
        alameda_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        self.assertEqual(result, alameda_pubdef)

    def test_get_receiving_agency_high_income_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        ebclc_high_income = dict(monthly_income=3000, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(ebclc_high_income)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        self.assertEqual(result, ebclc)

    def test_get_receiving_agency_owns_home_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        ebclc_owns_home = dict(monthly_income=2999, owns_home=field_types.YES)
        result = alameda.get_receiving_agency(ebclc_owns_home)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        self.assertEqual(result, ebclc)
