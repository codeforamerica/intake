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
        bundle = BundlesService.create_bundle_from_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)
        self.assertTrue(bundle.should_have_a_pdf())

    def test_should_have_a_pdf_negative(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = SubmissionsService.create_for_organizations(
                [cc_pubdef], answers={})
        bundle = BundlesService.create_bundle_from_submissions(
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
        bundle = BundlesService.create_bundle_from_submissions(
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
