from django.core.management.base import BaseCommand

import intake.services.bundles as BundlesService


class Command(BaseCommand):
    help = 'Sends an email about unopened applications'

    def handle(self, *args, **options):
        BundlesService.count_unreads_and_send_notifications_to_orgs()
        self.stdout.write(
            self.style.SUCCESS("Successfully referred any unopened apps")
        )
