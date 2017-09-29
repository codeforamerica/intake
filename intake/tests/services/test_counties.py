from django.test import TestCase
from user_accounts.models import Organization
from intake.models import County
import intake.services.counties as CountiesService


class TestGetLiveCountiesAndOrgs(TestCase):

    def test_doesnt_return_non_live_orgs(self):
        non_live_org = Organization(
            name="Vulcan High Council",
            is_receiving_agency=True)
        live_org = Organization(
            name="United Federation of Planets", is_live=True,
            is_receiving_agency=True)
        non_live_org.save()
        live_org.save()
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        self.assertNotIn(non_live_org, orgs)
        self.assertIn(live_org, orgs)

    def test_returns_counties_with_at_least_one_live_org(self):
        county = County.objects.first()
        non_live_org = Organization(
            name="Vulcan High Council", county=county,
            is_receiving_agency=True)
        live_org = Organization(
            name="United Federation of Planets", is_live=True,
            county=county, is_receiving_agency=True)
        non_live_org.save()
        live_org.save()
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        self.assertIn(county, counties)

    def test_doesnt_return_counties_with_no_live_orgs(self):
        live_county = County.objects.first()
        non_live_county = County.objects.last()
        non_live_org = Organization(
            name="Vulcan High Council", county=non_live_county,
            is_receiving_agency=True)
        live_org = Organization(
            name="United Federation of Planets", is_live=True,
            county=live_county, is_receiving_agency=True)
        non_live_org.save()
        live_org.save()
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        self.assertNotIn(non_live_county, counties)
        self.assertIn(live_county, counties)
