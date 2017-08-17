from django.core.management.base import BaseCommand
from dateutil.parser import parse

from intake import models


class Command(BaseCommand):
    help = "Fills dob column from answers['dob'] field"

    def handle(self, *args, **options):
        subs = models.FormSubmission.objects.filter(
            dob__isnull=True)
        migrated = 0
        for sub in subs:
            if not sub.dob:
                dob_obj = sub.answers['dob']
                parsed_dob = parse(
                    dob_obj['year']+'-'+dob_obj['month']+'-'+dob_obj['day'])

                sub.dob = parsed_dob
                sub.save(update_fields=['dob'])

                migrated += 1
        self.stdout.write(
            self.style.SUCCESS(
                "Updated dob on {} submissions".format(migrated))
        )
