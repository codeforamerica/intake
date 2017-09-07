import ntpath
from subprocess import Popen
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings
from .utils import aws_open


class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Downloads from s3 and loads data.")

    def handle(self, *args, **kwargs):
        sync_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'sync',
            's3://%s' % settings.ORIGIN_MEDIA_BUCKET_FOR_SYNC,
            's3://%s' % settings.AWS_STORAGE_BUCKET_NAME,
        ]
        aws_open(sync_s3)
        download_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            's3://%s/%s' % (
                settings.SYNC_BUCKET,
                ntpath.basename(settings.SYNC_FIXTURE_LOCATION),
            ),
            settings.SYNC_FIXTURE_LOCATION,
        ]
        aws_open(download_s3)
        management.call_command('flush', interactive=False)
        management.call_command('loaddata', settings.SYNC_FIXTURE_LOCATION)
