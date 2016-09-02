from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from intake import models


class Command(BaseCommand):

    help = "Creates FilledPDF instances for any submissions that need them."

    def handle(self, *args, **options):
        # get submissions that don't have any filled pdfs
        results = models.FilledPDF.objects.all().delete()
        self.stdout.write(str(results))
        for submission in models.FormSubmission.objects.all():
            counties = submission.counties.values_list('pk', flat=True)
            for fillable in models.FillablePDF.objects.filter(
                    organization__county__in=counties).all():
                pdf_bytes = fillable.fill(submission)
                pdf_file = SimpleUploadedFile('filled.pdf', pdf_bytes,
                                              content_type='application/pdf')
                filled_pdf = models.FilledPDF(
                    pdf=pdf_file,
                    original_pdf=fillable,
                    submission=submission,
                )
                filled_pdf.save()
                self.stdout.write(
                    "filled pdf {} for {}".format(
                        fillable.name, submission)
                    )
