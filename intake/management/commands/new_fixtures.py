from django.core.management.base import BaseCommand


from intake.tests import mock


class Command(BaseCommand):
    help = 'Generates new json sample fixtures'

    def handle(self, *args, **options):
        mock.build_seed_submissions()
        self.stdout.write(
            self.style.SUCCESS("Made some fake data")
        )
