from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = str(
        "Run commands required to set up a review application environment")

    def handle(self, *args, **kwargs):
        management.call_command('migrate', 'easyaudit')
        management.call_command('new_fixtures')
