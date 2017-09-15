from subprocess import Popen
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings
from .utils import aws_open


class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Dumps database and uploads to s3")

    def handle(self, *args, **kwargs):
        """Dumps a single full-database fixture to an S3 bucket for later use
        by ./manage.py download_data

        Relevant settings:
            SYNC_BUCKET - bucket to dump fixture to
            SYNC_FIXTURE_LOCATION - filename used for fixture
        """
        with open(settings.SYNC_FIXTURE_LOCATION, 'w+') as f:
            management.call_command(
                'dumpdata',
                natural_foreign=True,
                stdout=f,
            )
        upload_command = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            settings.SYNC_FIXTURE_LOCATION,  # local filename
            's3://%s' % settings.SYNC_BUCKET,  # bucket to upload to
        ]  # command for uploading to s3
        aws_open(upload_command)  # runs upload command
