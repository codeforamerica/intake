from unittest.mock import patch
from intake.tests.base_testcases import (
    IntakeDataTestCase, ALL_APPLICATION_FIXTURES)
from django.db.models import Count
from user_accounts import models, exceptions
from intake import models as intake_models
from user_accounts.tests import mock
from intake import constants


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
