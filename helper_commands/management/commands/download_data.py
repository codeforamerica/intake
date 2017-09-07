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
        # SYNC MEDIA FILES
        # sync s3 media bucket from one bucket another
        # overwrites files in the target bucket but does not delete
        # Relevant settings:
        #     ORIGIN_MEDIA_BUCKET_FOR_SYNC - bucket to pull from for sync
        #     AWS_STORAGE_BUCKET_NAME - bucket to overwrite with new files
        # args for sync command
        sync_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'sync',
            's3://%s' % settings.ORIGIN_MEDIA_BUCKET_FOR_SYNC,  # sync from
            's3://%s' % settings.AWS_STORAGE_BUCKET_NAME,  # sync to
        ]
        # run sync with aws env vars
        aws_open(sync_s3)

        # SYNC DATABASE
        # sync a large single database fixture:
        #    1. pull fixture from bucket to local tempfile
        #    2. empty existing database
        #    3. load local fixture tempfile
        # assumes that a db fixture has already been dumped to SYNC_BUCKET
        # by ./manage.py upload_data
        # Relevant settings:
        #     SYNC_BUCKET - bucket to pull fixture from
        #     SYNC_FIXTURE_LOCATION - filename used for fixture
        #
        # args for pulling fixture from bucket to local
        download_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            's3://%s/%s' % (
                settings.SYNC_BUCKET,  # bucket to pull from
                ntpath.basename(settings.SYNC_FIXTURE_LOCATION),  # filename
            ),
            settings.SYNC_FIXTURE_LOCATION,  # local temp filename
        ]
        # run command to pull down fixture to local file, with aws env vars
        aws_open(download_s3)
        management.call_command('flush', interactive=False)
        management.call_command('loaddata', settings.SYNC_FIXTURE_LOCATION)
