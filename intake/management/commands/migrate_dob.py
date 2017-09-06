from django.core.management.base import BaseCommand
from dateutil.parser import parse

from intake import models


class Command(BaseCommand):
    help = "Fills dob column from answers['dob'] field"

    def handle(self, *args, **options):
        subs = models.FormSubmission.objects.filter(dob__isnull=True)
        migrated = 0
        errored = 0
        for sub in subs:
            if not sub.dob:
                try:
                    dob_obj = sub.answers['dob']
                    parsed_dob = parse(("{year}-{month}-{day}").format(
                        year=dob_obj['year'],
                        month=dob_obj['month'],
                        day=dob_obj['day']))
                    sub.dob = parsed_dob
                    sub.save(update_fields=['dob'])
                    migrated += 1
                except Exception as e:
                    print(e)
                    print(vars(sub))
                    errored += 1
        self.stdout.write(self.style.SUCCESS(
                "Updated dob on {} submissions".format(migrated)))
        self.stdout.write(self.style.ERROR(
                "Failed to parse or update {} submissions".format(errored)))
