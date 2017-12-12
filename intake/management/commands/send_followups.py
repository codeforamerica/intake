from django.core.management.base import BaseCommand
import intake.services.followups as FollowupsService
from intake.utils import is_the_weekend


class Command(BaseCommand):
    help = 'Sends an email about unopened applications'

    def handle(self, *args, **options):
        if not is_the_weekend():
            FollowupsService.send_all_followups_that_are_due(after_id=465)
            self.stdout.write(
                self.style.SUCCESS("Successfully sent followups")
            )
