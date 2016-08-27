from django.test import TestCase
from unittest.mock import patch, Mock, call
from intake.tests import mock
from intake import models, submission_bundler


class BundlerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        counties = models.County.objects.order_by('slug').all()
        alameda = counties[0]
        contra_costa = counties[1]
        san_francisco = counties[2]
        # 6 submissions
        # 3 sf only
        # 2 cc only
        # 1 to sf & cc both
        county_sets = [
            [san_francisco],
            [san_francisco],
            [san_francisco],
            [san_francisco, contra_costa],
            [contra_costa],
            [contra_costa]]
        cls.sf = san_francisco
        cls.cc = contra_costa
        cls.submissions = []
        for county_set in county_sets:
            cls.submissions.append(
                mock.FormSubmissionFactory.create(
                    counties=county_set))

    def setUp(self):
        self.get_unopened_patcher = patch('.'.join([
            'intake.submission_bundler',
            'intake_models.FormSubmission',
            'get_unopened_apps',
        ]))
        self.log_referred_patcher = patch(
            'intake.submission_bundler.intake_models.ApplicationLogEntry.log_referred')
        self.notifications_patcher = patch(
            'intake.submission_bundler.notifications')

        self.log_referred = self.log_referred_patcher.start()
        self.notifications = self.notifications_patcher.start()

    def patch_unopened(self, return_value):
        unopened = self.get_unopened_patcher.start()
        unopened.return_value.prefetch_related.return_value.all.return_value = return_value

    def restore_unopened(self):
        self.get_unopened_patcher.stop()

    def tearDown(self):
        self.log_referred_patcher.stop()
        self.notifications_patcher.stop()


class TestOrganizationBundle(BundlerTestCase):

    def test_bundle_unopened_apps(self):
        bundler = submission_bundler.bundle_and_notify()
        self.assertEqual(
            self.notifications.front_email_daily_app_bundle.send.call_count, 2)
        self.assertEqual(
            self.notifications.slack_app_bundle_sent.send.call_count, 2)
        self.assertEqual(self.log_referred.call_count, 2)

    def test_bundle_with_no_unopened_apps(self):
        self.patch_unopened([])
        # mock out submissions
        self.notifications.front_email_daily_app_bundle.assert_not_called()
        self.notifications.slack_app_bundle_sent.assert_not_called()
        self.log_referred.assert_not_called()
        self.restore_unopened()


class TestSubmissionBundler(BundlerTestCase):

    def test_organization_bundle_map_with_no_referrals(self):
        self.patch_unopened([])
        bundler = submission_bundler.bundle_and_notify()
        self.assertEqual(bundler.organization_bundle_map, {})
        self.assertEqual(bundler.queryset, [])
        self.restore_unopened()

    def test_organization_bundle_map_with_referrals(self):
        bundler = submission_bundler.bundle_and_notify()
        self.assertEqual(len(bundler.queryset), 6)
        for org_bundle in bundler.organization_bundle_map.values():
            if org_bundle.organization.county == self.sf:
                self.assertEqual(
                    len(org_bundle.submissions), 4)
            elif org_bundle.organization.county == self.cc:
                self.assertEqual(
                    len(org_bundle.submissions), 3)
