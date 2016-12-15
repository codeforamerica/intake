import os
from unittest import skipUnless
from unittest.mock import patch, Mock, call

from django.test import TestCase


from intake.tests import mock
from user_accounts import models as auth_models
from intake import models, constants

import intake.services.submissions as SubmissionsService

import intake.services.bundles as BundlesService


DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


class TestApplicationBundle(TestCase):

    fixtures = ['counties', 'organizations']

    def test_should_have_a_pdf_positive(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        mock.fillable_pdf(organization=sf_pubdef)
        sub = SubmissionsService.create_for_organizations(
                [sf_pubdef], answers={})
        bundle = BundlesService.create_with_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)
        self.assertTrue(bundle.should_have_a_pdf())

    def test_should_have_a_pdf_negative(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = SubmissionsService.create_for_organizations(
                [cc_pubdef], answers={})
        bundle = BundlesService.create_with_submissions(
            organization=cc_pubdef, submissions=[sub], skip_pdf=True)
        self.assertFalse(bundle.should_have_a_pdf())

    def test_get_individual_filled_pdfs(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        subs = [
            SubmissionsService.create_for_organizations(
                [sf_pubdef], answers={})
            for i in range(2)]
        expected_pdfs = [
            models.FilledPDF(original_pdf=fillable, submission=sub)
            for sub in subs]
        for pdf in expected_pdfs:
            pdf.save()
        bundle = BundlesService.create_with_submissions(
            organization=sf_pubdef, submissions=subs, skip_pdf=True)
        query = bundle.get_individual_filled_pdfs().order_by('pk')
        pdfs = list(query)
        self.assertListEqual(pdfs, expected_pdfs)

    def test_get_absolute_url(self):
        org = auth_models.Organization.objects.first()
        bundle = models.ApplicationBundle(
            organization=org)
        bundle.save()
        expected_url = "/applications/bundle/{}/".format(bundle.id)
        result = bundle.get_absolute_url()
        self.assertEqual(result, expected_url)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_calls_pdfparser_correctly(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        subs = [
            SubmissionsService.create_for_organizations(
                [sf_pubdef],
                answers=mock.fake.cleaned_sf_county_form_answers())
            for i in range(2)]
        pdfs = [fillable.fill_for_submission(sub) for sub in subs]
        parser = models.get_parser()
        result = parser.join_pdfs(filled.pdf for filled in pdfs)
        self.assertTrue(len(result) > 30000)

    def test_build_bundled_pdf_with_no_filled_pdfs(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = SubmissionsService.create_for_organizations(
                [cc_pubdef], answers={})
        bundle = BundlesService.create_with_submissions(
            organization=cc_pubdef, submissions=[sub], skip_pdf=True)
        get_pdfs_mock = Mock()
        bundle.get_individual_filled_pdfs = get_pdfs_mock
        bundle.build_bundled_pdf_if_necessary()
        get_pdfs_mock.assert_not_called()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
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
        bundle = BundlesService.create_with_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)

        # set up mocks
        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=[filled])
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs

        # run method
        bundle.build_bundled_pdf_if_necessary()

        # check results
        get_parser.assert_not_called()
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()
        self.assertEqual(bundle.bundled_pdf.read(), data)

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdf_if_has_pdfs(self, logger, get_parser, slack):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        subs = [
            SubmissionsService.create_for_organizations(
                [sf_pubdef], answers={})
            for i in range(2)]

        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=['pdf' for sub in subs])
        get_parser.return_value.join_pdfs.return_value = b'pdf'

        bundle = BundlesService.create_with_submissions(
            organization=sf_pubdef, submissions=subs, skip_pdf=True)
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs
        bundle.build_bundled_pdf_if_necessary()
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.models.application_bundle.SubmissionsService')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdfs_if_not_prefilled(
            self, logger, get_parser, SimpleUploadedFile, SubmissionsService,
            slack):
        # given a bundle that should have a pdf
        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(return_value=[])
        # two submissions
        mock_submissions = Mock(**{'all.return_value': [Mock(), Mock()]})
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        # a bundle
        mock_bundle = Mock(
            pk=2,
            should_have_a_pdf=should_have_a_pdf,
            get_individual_filled_pdfs=get_individual_filled_pdfs,
            submissions=mock_submissions)
        mock_bundle.organization.pk = 1
        BundlesService.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(len(get_individual_filled_pdfs.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.models.application_bundle.SubmissionsService')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdfs_if_some_are_not_prefilled(
            self, logger, get_parser, SubmissionsService,
            SimpleUploadedFile, slack):
        should_have_a_pdf = Mock(return_value=True)
        mock_filled_pdf = Mock()
        # one existing pdf
        get_individual_filled_pdfs = Mock(return_value=[mock_filled_pdf])
        # two submissions
        mock_submissions = [Mock(), Mock()]
        mock_submissions_field = Mock(**{'all.return_value': mock_submissions})
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        mock_bundle = Mock(
            pk=2,
            should_have_a_pdf=should_have_a_pdf,
            get_individual_filled_pdfs=get_individual_filled_pdfs,
            submissions=mock_submissions_field)
        mock_bundle.organization.pk = 1
        # run
        BundlesService.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(len(get_individual_filled_pdfs.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()
        SubmissionsService.fill_pdfs_for_submission.assert_has_calls(
            [call(mock_sub) for mock_sub in mock_submissions], any_order=True)
