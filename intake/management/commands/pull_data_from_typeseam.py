import os

from django.conf import settings
from django.core.management.base import BaseCommand

from intake.management.data_import import DataImporter
from intake import notifications


class Command(BaseCommand):
    help = 'Imports data from a designated database connection url'

    def handle(self, *args, **options):
        importer = DataImporter(
            import_from=os.environ.get('IMPORT_DATABASE_URL', ''),
            ssl=True
        )
        importer.import_records(delete_existing=True)
        results = importer.report()
        self.stdout.write(results)
        notifications.slack_simple.send(results)
