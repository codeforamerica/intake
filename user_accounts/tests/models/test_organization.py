from intake.tests.base_testcases import (
    IntakeDataTestCase, ALL_APPLICATION_FIXTURES)
from user_accounts import models, exceptions
from user_accounts.tests import mock
from user_accounts.tests.factories import FakeOrganizationFactory


class TestOrganization(IntakeDataTestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_has_a_pdf(self):
        self.assertTrue(self.sf_pubdef.has_a_pdf())
        self.assertFalse(self.cc_pubdef.has_a_pdf())

    def test_get_referral_emails_even_if_no_users(self):
        expected_email = "foo@bar.net"
        # we need an org
        org = models.Organization(name="Acme Nonprofit Services Inc.")
        org.save()
        user = mock.fake_superuser()
        models.Invitation.create(
            expected_email,
            organization=org,
            inviter=user)
        emails = org.get_referral_emails()
        self.assertListEqual(emails, [expected_email])

    def test_get_referral_emails_raises_error_with_no_emails(self):
        org = models.Organization(name="Acme Nonprofit Services Inc.")
        org.save()
        with self.assertRaises(exceptions.NoEmailsForOrgError):
            org.get_referral_emails()

    def test_transfer_partners_returns_correct_org(self):
        ebclc = self.ebclc
        a_pubdef = self.a_pubdef
        self.assertIn(a_pubdef, ebclc.transfer_partners.all())
        self.assertIn(ebclc, a_pubdef.transfer_partners.all())

    def test_get_transfer_org_returns_none(self):
        sf_pubdef = self.sf_pubdef
        cc_pubdef = self.cc_pubdef
        self.assertFalse(sf_pubdef.transfer_partners.all())
        self.assertFalse(cc_pubdef.transfer_partners.all())

    def test_get_visible_set_returns_only_live_orgs_when_only_show_live_counties_is_true(self):
        live_org = FakeOrganizationFactory(is_live=True)
        non_receiving_org = FakeOrganizationFactory(is_live=True, is_receiving_agency=False)
        not_live_org = FakeOrganizationFactory(is_live=False)

        with self.settings(ONLY_SHOW_LIVE_COUNTIES=True):
            results = models.Organization.objects.get_visible_set()
            self.assertIn(live_org, results)
            self.assertNotIn(non_receiving_org, results)
            self.assertNotIn(not_live_org, results)

    def test_get_visible_set_returns_only_live_orgs_when_only_show_live_counties_is_false(self):
        live_org = FakeOrganizationFactory(is_live=True)
        non_receiving_org = FakeOrganizationFactory(is_live=True, is_receiving_agency=False)
        not_live_org = FakeOrganizationFactory(is_live=False)

        with self.settings(ONLY_SHOW_LIVE_COUNTIES=False):
            results = models.Organization.objects.get_visible_set()
            self.assertIn(live_org, results)
            self.assertIn(non_receiving_org, results)
            self.assertIn(not_live_org, results)
