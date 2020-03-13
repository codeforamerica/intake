from django.core import management
from django.core.management.base import BaseCommand
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES


class Command(BaseCommand):
    help = str(
        "Loads 'essential' data from fixture files")

    def handle(self, *args, **kwargs):
        management.call_command('loaddata', *ESSENTIAL_DATA_FIXTURES)
