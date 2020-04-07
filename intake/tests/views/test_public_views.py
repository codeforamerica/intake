from django.test import TestCase
from django.urls import reverse
from django.utils import html as html_utils

from intake import models
from user_accounts import models as auth_models


class TestFooterContent(TestCase):

    def test_footer_contains_login_link(self):
        response = self.client.get(reverse('intake-home'))
        self.assertContains(
            response,
            html_utils.conditional_escape(reverse('account_login')))


class TestPartnerListView(TestCase):
    fixtures = ['counties', 'organizations']

    def test_returns_200_with_org_name_list(self):
        response = self.client.get(reverse('intake-partner_list'))
        orgs = auth_models.Organization.objects.filter(
            is_live=True)
        self.assertEqual(response.status_code, 200)
        for org in orgs:
            self.assertContains(
                response, html_utils.conditional_escape(org.name))

    def test_doesnt_show_nonlive_partners(self):
        county = models.County.objects.first()
        live_org = auth_models.Organization(
            name='Starfleet',
            slug='starfleet',
            county=county,
            is_receiving_agency=True,
            is_live=True,
        )
        not_live_org = auth_models.Organization(
            name="Jem'Hadar",
            slug='jem-hadar',
            county=county,
            is_receiving_agency=True,
            is_live=False,
        )
        live_org.save()
        not_live_org.save()
        with self.settings(ONLY_SHOW_LIVE_COUNTIES=True):
            response = self.client.get(reverse('intake-partner_list'))
            self.assertContains(
                response,
                html_utils.conditional_escape(live_org.get_absolute_url()))
            self.assertNotContains(
                response,
                html_utils.conditional_escape(not_live_org.get_absolute_url()))

    def test_shows_nonlive_partners_if_live_county_choices_is_false(self):
        county = models.County.objects.first()
        live_org = auth_models.Organization(
            name='Starfleet',
            slug='starfleet',
            county=county,
            is_receiving_agency=True,
            is_live=True,
        )
        not_live_org = auth_models.Organization(
            name="Jem'Hadar",
            slug='jem-hadar',
            county=county,
            is_receiving_agency=True,
            is_live=False,
        )
        live_org.save()
        not_live_org.save()

        with self.settings(ONLY_SHOW_LIVE_COUNTIES=False):
            response = self.client.get(reverse('intake-partner_list'))
            for org in [live_org, not_live_org]:
                self.assertContains(
                    response, html_utils.conditional_escape(org.name))


class TestPartnerDetailView(TestCase):
    fixtures = ['counties', 'organizations']

    def test_returns_200_with_org_details(self):
        sf_pubdef = auth_models.Organization.objects.get(slug='sf_pubdef')
        response = self.client.get(
            reverse(
                'intake-partner_detail',
                kwargs=dict(organization_slug=sf_pubdef.slug)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sf_pubdef.phone_number)
        self.assertContains(response, html_utils.escape(sf_pubdef.blurb))
        self.assertContains(response, sf_pubdef.name)


class TestRecommendationLettersView(TestCase):

    def test_returns_200(self):
        response = self.client.get(reverse('intake-recommendation_letters'))
        self.assertEqual(response.status_code, 200)
