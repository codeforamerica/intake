from django.test import TestCase
from intake.tests.test_views import IntakeDataTestCase
from user_accounts import models
from intake import models as intake_models
from intake import constants
from user_accounts.tests import mock


class TestUserProfile(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_cc_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_cc_pubdef',
    ]

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sf_pubdef_user.profile.should_see_pdf())
        self.assertTrue(self.cfa_user.profile.should_see_pdf())
        self.assertFalse(self.cc_pubdef_user.profile.should_see_pdf())

    def test_should_have_access_to_allows_staff_submission_access(self):
        for sub in self.submissions:
            self.assertTrue(self.cfa_user.profile.should_have_access_to(sub))

    def test_should_have_access_to_limits_submission_access_same_org(self):
        for sub in self.sf_pubdef_submissions:
            self.assertTrue(
                self.sf_pubdef_user.profile.should_have_access_to(sub))
            self.assertFalse(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
        for sub in self.cc_pubdef_submissions:
            self.assertFalse(
                self.sf_pubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
        for sub in self.combo_submissions:
            self.assertTrue(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.sf_pubdef_user.profile.should_have_access_to(sub))

    def should_have_access_to_allows_staff_submission_access(self):
        bundle = self.cc_pubdef_bundle
        self.assertTrue(self.cfa_user.profile.should_have_access_to(bundle))
        self.assertTrue(
            self.cc_pubdef_user.profile.should_have_access_to(bundle))
        self.assertFalse(
            self.sf_pubdef_user.profile.should_have_access_to(bundle))

    def should_have_access_to_raises_error_for_other_objects(self):
        with self.assertRaises(models.UndefinedResourceAccessError):
            self.cfa_user.profile.should_have_access_to({})


class TestOrganization(IntakeDataTestCase):

    fixtures = ['organizations', 'mock_profiles']

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
        with self.assertRaises(models.NoEmailsForOrgError):
            org.get_referral_emails()

    def test_get_transfer_org_returns_correct_org(self):
        ebclc = self.ebclc
        a_pubdef = self.a_pubdef
        self.assertEqual(ebclc.get_transfer_org(), a_pubdef)
        self.assertEqual(a_pubdef.get_transfer_org(), ebclc)

    def test_get_transfer_org_returns_none(self):
        sf_pubdef = self.sf_pubdef
        cc_pubdef = self.cc_pubdef
        self.assertIsNone(sf_pubdef.get_transfer_org())
        self.assertIsNone(cc_pubdef.get_transfer_org())


class TestAddress(TestCase):

    def test_can_create_without_walk_in_hours(self):
        a_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        address = models.Address(
            organization=a_pubdef,
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertTrue(address.id)

    def test_can_create_with_walk_in_hours(self):
        a_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        address = models.Address(
            organization=a_pubdef,
            walk_in_hours="Every Tuesday, from 2pm to 4pm",
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertTrue(address.id)

    def can_get_addresses_of_organization(self):
        a_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        address = models.Address(
            organization=a_pubdef,
            walk_in_hours="Every Tuesday, from 2pm to 4pm",
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertEqual(address.organization, a_pubdef)
        self.assertListEqual(
            list(a_pubdef.addresses.all()),
            [address])
