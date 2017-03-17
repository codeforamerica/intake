from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = str(
        "Sets up seeds based on what environment it runs in.")

    def handle(self, *args, **kwargs):
        management.call_command(
            'loaddata',
            'counties',
            'organizations',
            'addresses',
            'groups',
            'template_options')
