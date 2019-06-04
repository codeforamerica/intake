from django.core.management import BaseCommand

from intake.tests.mock import build_2000_mock_submissions


class Command(BaseCommand):
    help = 'Generates new json sample fixtures'

    def handle(self, *args, **options):
        build_2000_mock_submissions()
        self.stdout.write(
            self.style.SUCCESS(
                "Created fake submissions, bundles, and transfers "
                "and saved them to fixture files"))
