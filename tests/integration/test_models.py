from django.test import TestCase
from datetime import datetime

from tests.factories import FormSubmissionFactory
from intake.models import FormSubmission, FillablePDF

class TestModels(TestCase):

    def test_submission(self):
        submission = FormSubmissionFactory()
        self.assertEqual(int, type(submission.id))
        self.assertEqual(datetime, type(submission.date_received))
        self.assertEqual(dict, type(submission.answers))
        self.assertEqual(
            FormSubmission.objects.get(id=submission.id), submission)

    def test_fillablepdf(self):
        from django.core.files import File
        sample_pdf_path = 'tests/sample_pdfs/sample_form.pdf'
        pdf = FillablePDF(
            name="Sample_pdf",
            pdf=File(open(sample_pdf_path, 'rb')),
            translator='tests.sample_translator.translate'
            )
        fields = pdf.get_pdf_fields()
        self.assertEqual(type(fields), list)
        filled_pdf = pdf.fill({'Given Name Text Box': 'Ben'})
        self.assertEqual(type(filled_pdf), bytes)
    
