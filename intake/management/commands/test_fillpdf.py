from django.core import management
from django.core.management.base import BaseCommand

from intake.models import pdfs
from intake.models import form_submission


class Command(BaseCommand):
    help = str(
        "Sets up seeds based on what environment it runs in.")

    def handle(self, *args, **kwargs):
        fillable = pdfs.FillablePDF.objects.first()
        sub = form_submission.FormSubmission.objects.first()
        filled = fillable.fill_for_submission(sub)
        print(filled)
