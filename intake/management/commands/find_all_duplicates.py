from django.core.management.base import BaseCommand

from intake import models
import intake.services.submissions as SubmissionsService


class Command(BaseCommand):
    help = str(
        "Finds all duplicate submissions and saves them as "
        "DuplicateSubmissionSet objects")

    def handle(self, *args, **options):
        dup_sets = SubmissionsService.find_duplicates(
            models.FormSubmission.objects.all())
        self.stdout.write("Found {} duplicate sets".format(len(dup_sets)))
        existing_dup_sets = models.DuplicateSubmissionSet.objects.all()
        self.stdout.write("{} duplicate sets already exist".format(
            existing_dup_sets.count()))
        count_already_existed = 0
        dup_set_extensions = {}
        new_dup_sets = []
        existing_dup_set_lookups = {
            frozenset(dup_set.submissions.all()): dup_set
            for dup_set in existing_dup_sets
        }
        for dup_set in dup_sets:
            found_existing = False
            for lookup_set, existing in existing_dup_set_lookups.items():
                if dup_set == lookup_set:
                    found_existing = True
                    count_already_existed += 1
                    break
                elif dup_set & lookup_set:
                    dup_set_extensions[existing] = dup_set
                    found_existing = True
                    break
            if not found_existing:
                new_dup_sets.append(dup_set)
        for existing, new_dups in dup_set_extensions:
            existing.submissions.add(*new_dups)
        self.stdout.write(
            "{} found duplicate sets were existing".format(
                count_already_existed))
        self.stdout.write("Extended {} existing duplicate sets".format(
            len(dup_set_extensions)))
        for new_set in new_dup_sets:
            new_dup_set_object = models.DuplicateSubmissionSet()
            new_dup_set_object.save()
            new_dup_set_object.submissions.add(*new_set)
        self.stdout.write("Created {} new duplicate sets".format(
            len(new_dup_sets)))
