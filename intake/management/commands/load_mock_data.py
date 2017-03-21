from django.core import management
from django.core.management.base import BaseCommand
from intake.models import pdfs
from intake.tests import mock
from project.fixtures_index import ALL_MOCK_DATA_FIXTURES


class Command(BaseCommand):
    help = str(
        "Sets up seeds based on what environment it runs in.")

    def handle(self, *args, **kwargs):
        management.call_command(
            'loaddata', *ALL_MOCK_DATA_FIXTURES)
        if pdfs.FillablePDF.objects.count() == 0:
            mock.fillable_pdf()
