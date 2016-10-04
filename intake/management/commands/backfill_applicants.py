from django.core.management.base import BaseCommand

from intake import models


class Command(BaseCommand):
    help = 'Backfills applicant_id on FormSubmissions if null'

    def handle(self, *args, **options):
        subs = models.FormSubmission.objects.filter(
            applicant_id__isnull=True)
        backfilled = 0
        for sub in subs:
            if not sub.applicant_id:
                applicant = models.Applicant()
                applicant.save()
                sub.applicant = applicant
                sub.save()
                models.ApplicationEvent(
                    applicant_id=applicant.id,
                    name=models.ApplicationEvent.APPLICATION_SUBMITTED,
                    time=sub.date_received)
                backfilled += 1
        self.stdout.write(
            self.style.SUCCESS(
                "Backfilled applicants on {} submissions".format(backfilled))
        )
