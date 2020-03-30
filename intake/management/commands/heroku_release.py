from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = str(
        "Migrates and loads essential data from fixtures")

    def handle(self, *args, **kwargs):
        management.call_command('migrate')
        management.call_command('load_essential_data')
