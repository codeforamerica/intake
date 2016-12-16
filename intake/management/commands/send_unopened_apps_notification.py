from django.core.management.base import BaseCommand

from intake import submission_bundler


class Command(BaseCommand):
    help = 'Sends an email about unopened applications'

    def handle(self, *args, **options):
        submission_bundler.bundle_and_notify()
        self.stdout.write(
            self.style.SUCCESS("Successfully referred any unopened apps")
        )
