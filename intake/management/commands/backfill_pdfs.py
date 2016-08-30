from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from intake import models


class Command(BaseCommand):

    help = "Creates FilledPDF instances for any submissions that need them."

    def handle(self, *args, **options):
        # get submissions that don't have any filled pdfs
        for submission in models.FormSubmission.objects.filter(
                filled_pdfs=None):
            counties = submission.counties.values_list('pk', flat=True)
            for pdf in models.FillablePDF.objects.filter(
                    organization__county__in=counties).all():
                pdf_bytes = pdf.fill(submission)
                pdf_file = SimpleUploadedFile('filled.pdf', pdf_bytes,
                                              content_type='application/pdf')
                filled_pdf = models.FilledPDF(
                    pdf=pdf_file,
                    original_pdf=pdf,
                    submission=submission,
                )
                filled_pdf.save()
