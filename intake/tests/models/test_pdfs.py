from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from intake import models, constants
from user_accounts import models as auth_models
import intake.services.submissions as SubmissionsService


class TestFilledPDF(TestCase):

    def test_get_absolute_url(self):
        org = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = SubmissionsService.create_for_organizations([org], answers={})
        expected_url = "/application/{}/pdf/".format(sub.id)
        filled = models.FilledPDF(submission=sub)
        self.assertEqual(filled.get_absolute_url(), expected_url)

    def test_save_binary_data_to_pdf(self):
        org = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = SubmissionsService.create_for_organizations([org], answers={})
        data = b'content'
        fob = SimpleUploadedFile(
            content=data, name="content.pdf", content_type="application/pdf")
        filled = models.FilledPDF(submission=sub, pdf=fob)
        filled.save()
        self.assertEqual(filled.pdf.read(), data)
        self.assertIn("content", filled.pdf.name)
        self.assertIn(".pdf", filled.pdf.name)
