from django.core import management
from django.core.management.base import BaseCommand
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES


class Command(BaseCommand):
    help = str(
        "Sets up seeds based on what environment it runs in.")

    def handle(self, *args, **kwargs):
        management.call_command('loaddata', *ESSENTIAL_DATA_FIXTURES)
