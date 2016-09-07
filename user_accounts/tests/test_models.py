from django.test import TestCase
from intake.tests.test_views import IntakeDataTestCase
from user_accounts import models
from user_accounts.tests import mock


class TestUserProfile(IntakeDataTestCase):

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sfpubdef_user.profile.should_see_pdf())
        self.assertTrue(self.cfa_user.profile.should_see_pdf())
        self.assertFalse(self.ccpubdef_user.profile.should_see_pdf())

    def test_should_have_access_to(self):
        for sub in self.submissions:
            self.assertTrue(self.cfa_user.profile.should_have_access_to(sub))
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


class TestOrganization(IntakeDataTestCase):

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