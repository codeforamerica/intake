from intake.tests.test_views import IntakeDataTestCase
from user_accounts import models
from intake import models as intake_models
from intake import constants
from user_accounts.tests import mock


class TestUserProfile(IntakeDataTestCase):

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sfpubdef_user.profile.should_see_pdf())
        self.assertTrue(self.cfa_user.profile.should_see_pdf())
        self.assertFalse(self.ccpubdef_user.profile.should_see_pdf())

    def test_should_have_access_to_allows_staff_submission_access(self):
        for sub in self.submissions:
            self.assertTrue(self.cfa_user.profile.should_have_access_to(sub))

    def test_should_have_access_to_limits_submission_access_same_org(self):
        for sub in self.sf_submissions:
            self.assertTrue(
                self.sfpubdef_user.profile.should_have_access_to(sub))
            self.assertFalse(
                self.ccpubdef_user.profile.should_have_access_to(sub))
        for sub in self.cc_submissions:
            self.assertFalse(
                self.sfpubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.ccpubdef_user.profile.should_have_access_to(sub))
        for sub in self.combo_submissions:
            self.assertTrue(
                self.ccpubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.sfpubdef_user.profile.should_have_access_to(sub))

    def should_have_access_to_allows_staff_submission_access(self):
        bundle = intake_models.ApplicationBundle.create_with_submissions(
            submissions=self.cc_submissions,
            organization=self.cc_pubdef,
            skip_pdf=True
            )
        self.assertTrue(self.cfa_user.profile.should_have_access_to(bundle))
        self.assertTrue(
            self.ccpubdef_user.profile.should_have_access_to(bundle))
        self.assertFalse(
            self.sfpubdef_user.profile.should_have_access_to(bundle))

    def should_have_access_to_raises_error_for_other_objects(self):
        with self.assertRaises(models.UndefinedResourceAccessError):
            self.cfa_user.profile.should_have_access_to({})


class TestOrganization(IntakeDataTestCase):

    fixtures = ['organizations']

    def test_has_a_pdf(self):
        self.assertTrue(self.sfpubdef.has_a_pdf())
        self.assertFalse(self.ccpubdef.has_a_pdf())

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
        ebclc = models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        a_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        self.assertEqual(ebclc.get_transfer_org(), a_pubdef)
        self.assertEqual(a_pubdef.get_transfer_org(), ebclc)

    def test_get_transfer_org_returns_none(self):
        sf_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        cc_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        self.assertIsNone(sf_pubdef.get_transfer_org())
        self.assertIsNone(cc_pubdef.get_transfer_org())


