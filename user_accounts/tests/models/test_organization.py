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

    def test_get_unopened_apps_returns_all_apps_if_no_open_events(self):
        ebclc = models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        for org in models.Organization.objects.filter(
                is_receiving_agency=True):
            if org == ebclc:
                self.assertEqual(org.get_unopened_apps().count(), 2)
            else:
                self.assertEqual(org.get_unopened_apps().count(), 3)

    def test_get_unopened_apps_returns_apps_opened_by_other_org(self):
        # assume we have a multi-org app opened by a user from one org
        cc_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        a_pubdef = models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        cc_pubdef_user = models.UserProfile.objects.filter(
                organization=cc_pubdef).first().user
        sub = intake_models.FormSubmission.objects.annotate(
            org_count=Count('organizations')).filter(org_count__gte=3).first()
        intake_models.ApplicationLogEntry.log_opened([sub.id], cc_pubdef_user)
        # assert that it shows up in unopened apps
        self.assertIn(sub, a_pubdef.get_unopened_apps())
        self.assertNotIn(sub, cc_pubdef.get_unopened_apps())

    @patch('intake.models.ApplicationEvent.from_logs')
    def test_get_unopened_apps_with_deleted_opened_app_returns_expected_result(
            self, from_logs):
        # https://code.djangoproject.com/ticket/25467?cversion=0&cnum_hist=2
        logs = intake_models.ApplicationLogEntry.log_opened(
            [None], user=self.sf_pubdef_user)
        self.assertTrue(logs[0].id)
        self.assertIsNone(logs[0].submission_id)
        self.assertEqual(self.sf_pubdef.get_unopened_apps().count(), 3)
