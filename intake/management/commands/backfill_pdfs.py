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
            organizations = submission.organizations.values('pk')
            for fillable in models.FillablePDF.objects.filter(
                    organization__in=organizations).all():
                filled_pdf = fillable.fill_for_submission(submission)
                self.stdout.write(
                    "filled pdf {} for {}".format(
                        filled_pdf.pdf, submission)
                    )
