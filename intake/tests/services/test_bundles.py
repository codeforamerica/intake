from unittest.mock import Mock, patch, call
from django.test import TestCase

from project.jinja2 import external_reverse
import user_accounts.models as auth_models
from intake import constants, models
import intake.services.bundles as BundlesService
import intake.services.submissions as SubmissionsService
from intake.tests import mock
from user_accounts.tests.factories import UserProfileFactory
from intake.tests.factories import make_apps_for


def not_the_weekend():
    return False


def yes_its_the_weekend():
    return True


class TestBuildBundledPdfIfNecessary(TestCase):

    def test_build_bundled_pdf_with_no_filled_pdfs(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = SubmissionsService.create_for_organizations(
            [cc_pubdef], answers={})
        bundle = BundlesService.create_bundle_from_submissions(
            organization=cc_pubdef, submissions=[sub], skip_pdf=True)
        get_pdfs_mock = Mock()
        bundle.get_individual_filled_pdfs = get_pdfs_mock
        BundlesService.build_bundled_pdf_if_necessary(bundle)
        get_pdfs_mock.assert_not_called()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.get_parser')
    @patch('intake.services.bundles.logger')
    def test_build_bundled_pdf_with_one_pdf(self, logger, get_parser, slack):
        # set up associated data
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = SubmissionsService.create_for_organizations(
            [sf_pubdef], answers={})
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        data = b'content'
        filled = models.FilledPDF.create_with_pdf_bytes(
            pdf_bytes=data, submission=sub, original_pdf=fillable)
        bundle = BundlesService.create_bundle_from_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)

        # set up mocks
        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=[filled])
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs

        # run method
        BundlesService.build_bundled_pdf_if_necessary(bundle)

        # check results
        get_parser.assert_not_called()
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()
        self.assertEqual(bundle.bundled_pdf.read(), data)

    @patch('intake.services.bundles.SubmissionsService')
    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.services.bundles.get_parser')
    @patch('intake.services.bundles.logger')
    def test_build_bundled_pdfs_if_not_prefilled(
            self, logger, get_parser, SimpleUploadedFile, slack,
            SubService):
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        # a bundle
        mock_bundle = Mock(pk=2)
        mock_bundle.submissions.all.return_value = [Mock(), Mock()]
        mock_bundle.get_individual_filled_pdfs.return_value = []
        mock_bundle.should_have_a_pdf.return_value = True
        mock_bundle.organization.pk = 1
        BundlesService.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(
            len(mock_bundle.get_individual_filled_pdfs.mock_calls), 2)
        self.assertEqual(
            len(SubService.fill_pdfs_for_submission.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.services.bundles.get_parser')
    @patch('intake.services.bundles.logger')
    def test_build_bundled_pdf_if_has_pdfs(self, logger, get_parser, slack):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        subs = [
            SubmissionsService.create_for_organizations(
                [sf_pubdef], answers={})
            for i in range(2)]

        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=[Mock(pdf=b'pdf') for sub in subs])
        get_parser.return_value.join_pdfs.return_value = b'pdf'

        bundle = BundlesService.create_bundle_from_submissions(
            organization=sf_pubdef, submissions=subs, skip_pdf=True)
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs
        BundlesService.build_bundled_pdf_if_necessary(bundle)
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()

    @patch('intake.services.bundles.SubmissionsService')
    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.services.bundles.get_parser')
    @patch('intake.services.bundles.logger')
    def test_build_bundled_pdfs_if_some_are_not_prefilled(
            self, logger, get_parser, SimpleUploadedFile, slack,
            SubService):
        # two submissions
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        mock_submissions = [Mock(), Mock()]
        mock_bundle = Mock(pk=2)
        mock_bundle.should_have_a_pdf.return_value = True
        # one is not prefilled
        mock_bundle.get_individual_filled_pdfs.return_value = [Mock()]
        mock_bundle.submissions.all.return_value = mock_submissions
        mock_bundle.organization.pk = 1
        # run
        BundlesService.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(
            len(mock_bundle.get_individual_filled_pdfs.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()
        SubService.fill_pdfs_for_submission.assert_has_calls(
            [call(mock_sub) for mock_sub in mock_submissions], any_order=True)


class TestGetOrgsThatMightNeedABundleEmailToday(TestCase):

    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
    ]

    @patch('intake.services.bundles.is_the_weekend', not_the_weekend)
    def test_returns_orgs_iff_have_subs_and_profiles(self):
        expected_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        org_with_subs_but_no_user = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        # delete user_profiles for coco
        auth_models.UserProfile.objects.filter(
            organization=org_with_subs_but_no_user).delete()
        org_with_users_but_no_subs = auth_models.Organization.objects.get(
            slug=constants.Organizations.SAN_DIEGO_PUBDEF)
        org_without_users_or_subs = auth_models.Organization(
            name='New Org', slug='new_org', is_receiving_agency=True)
        org_without_users_or_subs.save()

        with self.assertNumQueries(1):
            org_results = set(
                BundlesService.get_orgs_that_might_need_a_bundle_email_today())

        self.assertIn(expected_org, org_results)
        self.assertNotIn(org_with_subs_but_no_user, org_results)
        self.assertNotIn(org_with_users_but_no_subs, org_results)
        self.assertNotIn(org_without_users_or_subs, org_results)

    @patch('intake.services.bundles.is_the_weekend', yes_its_the_weekend)
    def test_doesnt_return_some_orgs_on_the_weekend(self):
        weekend_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        weekend_org.notify_on_weekends = True
        weekend_org.save()
        # all the orgs are weekday only by default
        weekday_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        org_results = set(
            BundlesService.get_orgs_that_might_need_a_bundle_email_today())
        self.assertIn(weekend_org, org_results)
        self.assertNotIn(weekday_org, org_results)

    @patch('intake.services.bundles.is_the_weekend', not_the_weekend)
    def test_only_returns_orgs_that_check_notifications(self):
        expected_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        org_not_checking_notifications = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        org_not_checking_notifications.is_checking_notifications = False
        org_not_checking_notifications.save()
        org_results = set(
            BundlesService.get_orgs_that_might_need_a_bundle_email_today())
        self.assertIn(expected_org, org_results)
        self.assertNotIn(org_not_checking_notifications, org_results)


class TestCreateBundlesAndSendNotificationsToOrgs(TestCase):

    fixtures = [
        'counties', 'groups', 'organizations', 'mock_profiles',
        'template_options'
    ]

    def setUp(self):
        self.get_unopened_patcher = patch(
            'intake.services.bundles.SubmissionsService'
            '.get_unopened_submissions_for_org')
        self.notifications_patcher = patch(
            'intake.services.bundles.notifications')
        self.notifications = self.notifications_patcher.start()

    def patch_unopened(self, return_value):
        unopened = self.get_unopened_patcher.start()
        unopened.return_value = return_value

    def restore_unopened(self):
        self.get_unopened_patcher.stop()

    def tearDown(self):
        self.notifications_patcher.stop()

    @patch(
        'intake.services.bundles'
        '.get_orgs_that_might_need_a_bundle_email_today')
    @patch('intake.services.bundles.is_the_weekend', not_the_weekend)
    def test_queries_and_notifications_for_each_org(self, get_orgs):
        a_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        make_apps_for(a_pubdef.slug, count=3)
        # assume we only receive one org back
        get_orgs.return_value = [a_pubdef]
        with self.assertNumQueries(4):
            BundlesService.count_unreads_and_send_notifications_to_orgs()
        self.assertEqual(
            self.notifications.front_email_daily_app_bundle.send.call_count, 1)
        self.assertEqual(
            self.notifications.slack_app_bundle_sent.send.call_count, 1)


class TestCountUnreadsAndSendNotificationsToOrgs(TestCase):

    def email_and_org(self):
        profile = UserProfileFactory()
        return profile.user.email, profile.organization

    @patch('intake.notifications.front_email_daily_app_bundle.send')
    @patch('intake.notifications.slack_app_bundle_sent.send')
    @patch('intake.services.bundles.is_the_weekend', not_the_weekend)
    def test_counts_and_notification_args_for_unreads(self, slack, send_email):
        email, org = self.email_and_org()
        make_apps_for(org.slug, count=3, answers={})
        BundlesService.count_unreads_and_send_notifications_to_orgs()
        send_email.assert_called_once_with(
                to=[email],
                org_name=org.name,
                unread_count=3,
                update_count=3,
                all_count=3,
                unread_redirect_link=external_reverse(
                    'intake-unread_email_redirect'),
                needs_update_redirect_link=external_reverse(
                    'intake-needs_update_email_redirect'),
                all_redirect_link=external_reverse(
                    'intake-all_email_redirect'))
        slack.assert_called_once_with(
            org_name=org.name,
            emails=[email],
            unread_count=3,
            update_count=3,
            all_count=3)

    @patch('intake.notifications.front_email_daily_app_bundle.send')
    @patch('intake.notifications.slack_app_bundle_sent.send')
    @patch('intake.services.bundles.is_the_weekend', not_the_weekend)
    def test_counts_and_notification_args_for_no_unreads(
            self, slack, send_email):
        email, org = self.email_and_org()
        apps = make_apps_for(org.slug, count=3, answers={})
        for app in apps:
            app.has_been_opened = True
            app.save()
        BundlesService.count_unreads_and_send_notifications_to_orgs()
        send_email.assert_not_called()
        slack.assert_called_once_with(
            org_name=org.name,
            emails=[email],
            unread_count=0,
            update_count=3,
            all_count=3)
