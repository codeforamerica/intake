from unittest.mock import Mock, patch, call
from django.test import TestCase

import user_accounts.models as auth_models

from intake import constants, models
import intake.services.bundles as BundlesService
import intake.services.submissions as SubmissionsService

from intake.tests import mock


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
