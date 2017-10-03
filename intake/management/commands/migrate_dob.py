from django.core.management.base import BaseCommand
from datetime import date
from intake import models
from formation.fields import DateOfBirthField


class Command(BaseCommand):
    help = "Fills dob column from answers['dob'] field"

    def handle(self, *args, **options):
        subs = models.FormSubmission.objects.filter(dob__isnull=True)
        migrated = 0
        errored = 0
        for sub in subs:
            if not sub.dob:
                try:
                    field = DateOfBirthField(sub.answers)
                    if field.is_valid():
                        sub.dob = date(**field.get_current_value())
                        sub.save(update_fields=['dob'])
                        migrated += 1
                    else:
                        print(vars(sub))
                        errored += 1
                except Exception as e:
                    print(e)
                    print(vars(sub))
                    errored += 1
        self.stdout.write(self.style.SUCCESS(
                "Updated dob on {} submissions".format(migrated)))
        self.stdout.write(self.style.ERROR(
                "Failed to parse or update {} submissions".format(errored)))
