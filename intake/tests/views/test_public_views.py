from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import html as html_utils

from intake import constants
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
            is_receiving_agency=True)
        self.assertEqual(response.status_code, 200)
        for org in orgs:
            self.assertContains(
                response, html_utils.conditional_escape(org.name))


class TestPartnerDetailView(TestCase):
    fixtures = ['counties', 'organizations']

    def test_returns_200_with_org_details(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
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
