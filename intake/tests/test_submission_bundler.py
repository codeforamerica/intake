from django.test import TestCase
from unittest.mock import patch
from django.db.models import Count
from intake import models, submission_bundler
from user_accounts.models import Organization, UserProfile


def not_the_weekend():
    return False


def yes_it_is():
    return True


class BundlerTestCase(TestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_sf_pubdef',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_cc_pubdef',
        'mock_2_submissions_to_ebclc',
        'mock_2_submissions_to_monterey_pubdef',
        'mock_1_submission_to_multiple_orgs',
    ]

    def setUp(self):
        self.get_unopened_patcher = patch('.'.join([
            'intake.submission_bundler',
            'Organization',
            'get_unopened_apps',
        ]))
        self.log_referred_patcher = patch(
            'intake.submission_bundler.intake_models'
            '.ApplicationLogEntry.log_referred')
        self.notifications_patcher = patch(
            'intake.submission_bundler.notifications')

        self.log_referred = self.log_referred_patcher.start()
        self.notifications = self.notifications_patcher.start()

    def patch_unopened(self, return_value):
        unopened = self.get_unopened_patcher.start()
        unopened.return_value = return_value

    def restore_unopened(self):
        self.get_unopened_patcher.stop()

    def tearDown(self):
        self.log_referred_patcher.stop()
        self.notifications_patcher.stop()


class TestOrganizationBundle(BundlerTestCase):

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_bundle_unopened_apps(self, *args):
        receiving_org_count = Organization.objects.filter(
            is_receiving_agency=True).count()
        submission_bundler.bundle_and_notify()
        self.assertEqual(
            self.notifications.front_email_daily_app_bundle.send.call_count,
            receiving_org_count)
        self.assertEqual(
            self.notifications.slack_app_bundle_sent.send.call_count,
            receiving_org_count)
        self.assertEqual(
            self.log_referred.call_count, receiving_org_count)
        bundles = models.ApplicationBundle.objects.all()
        self.assertEqual(bundles.count(), receiving_org_count)

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_bundle_with_no_unopened_apps(self, *args):
        self.patch_unopened([])
        submission_bundler.bundle_and_notify()
        self.notifications.front_email_daily_app_bundle.assert_not_called()
        self.notifications.slack_app_bundle_sent.assert_not_called()
        self.log_referred.assert_not_called()
        self.restore_unopened()


class TestSubmissionBundler(BundlerTestCase):

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_get_orgs_that_should_get_emails_today_on_weekday(self, *args):
        all_orgs = set(Organization.objects.filter(
            is_receiving_agency=True))
        bundler = submission_bundler.SubmissionBundler()
        todays_orgs = set(bundler.get_orgs_that_should_get_emails_today())
        self.assertEqual(all_orgs, todays_orgs)

    @patch('intake.submission_bundler.is_the_weekend', yes_it_is)
    def test_get_orgs_that_should_get_emails_today_on_weekend(self, *args):
        modified_org = Organization.objects.filter(
            is_receiving_agency=True).first()
        modified_org.notify_on_weekends = True
        modified_org.save()
        bundler = submission_bundler.SubmissionBundler()
        todays_orgs = list(bundler.get_orgs_that_should_get_emails_today())
        self.assertEqual([modified_org], todays_orgs)

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_organization_bundle_map_with_no_referrals(self, *args):
        self.patch_unopened([])
        bundler = submission_bundler.bundle_and_notify()
        for bundle in bundler.organization_bundle_map.values():
            self.assertEqual(len(bundle.submissions), 0)
        self.restore_unopened()

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_organization_bundle_map_with_referrals(self, *args):
        sf_pubdef = Organization.objects.get(slug='sf_pubdef')
        cc_pubdef = Organization.objects.get(slug='cc_pubdef')
        bundler = submission_bundler.bundle_and_notify()
        for org_bundle in bundler.organization_bundle_map.values():
            if org_bundle.organization == sf_pubdef:
                self.assertEqual(
                    len(org_bundle.submissions), 3)
            elif org_bundle.organization == cc_pubdef:
                self.assertEqual(
                    len(org_bundle.submissions), 3)

    @patch('intake.submission_bundler.is_the_weekend', not_the_weekend)
    def test_opening_multi_org_sub_removes_only_from_org_of_user(self, *args):
        sf_pubdef = Organization.objects.get(slug='sf_pubdef')
        cc_pubdef = Organization.objects.get(slug='cc_pubdef')
        a_pubdef = Organization.objects.get(slug='a_pubdef')
        ebclc = Organization.objects.get(slug='ebclc')
        ebclc_user = UserProfile.objects.filter(
            organization=ebclc).first().user
        sub = models.FormSubmission.objects.annotate(
            org_count=Count('organizations')).filter(org_count__gte=3).first()
        models.ApplicationLogEntry.log_opened([sub.id], ebclc_user)
        bundler = submission_bundler.bundle_and_notify()
        a_pubdef_subs = bundler.organization_bundle_map.get(
            a_pubdef.id).submissions
        cc_pubdef_subs = bundler.organization_bundle_map.get(
            cc_pubdef.id).submissions
        sf_pubdef_subs = bundler.organization_bundle_map.get(
            sf_pubdef.id).submissions
        ebclc_subs = bundler.organization_bundle_map.get(
            ebclc.id).submissions
        self.assertEqual(len(a_pubdef_subs), 3)
        self.assertEqual(len(cc_pubdef_subs), 3)
        self.assertEqual(len(sf_pubdef_subs), 3)
        self.assertEqual(len(ebclc_subs), 2)
