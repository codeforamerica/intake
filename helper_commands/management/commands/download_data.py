import ntpath
from subprocess import Popen
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings
from .utils import aws_open, run_sql, pg_load


class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Downloads from s3 and loads data.")

    def handle(self, *args, **kwargs):
        """Downloads a single full-database fixture into db and syncs s3
        by ./manage.py download_data

        1. sync replica from origin
        2. pull fixture from bucket to local tempfile
        3. empty existing database
        4. load local fixture tempfile

        Relevant settings:
            ORIGIN_MEDIA_BUCKET_FOR_SYNC - bucket to pull from for sync
            AWS_STORAGE_BUCKET_NAME - bucket to overwrite with new files
            SYNC_BUCKET - bucket to pull fixture from
            SYNC_FIXTURE_LOCATION - filename used for fixture

        Assumes that a db fixture has already been dumped to SYNC_BUCKET
        by ./manage.py upload_data
        Relevant settings:
        """
        if not settings.ORIGIN_MEDIA_BUCKET_FOR_SYNC:
            raise Exception(
                "Warning: ORIGIN_MEDIA_BUCKET_FOR_SYNC not set."
                "Its likely this is production. This Error has protected you.")
        sync_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'sync',
            's3://%s' % settings.ORIGIN_MEDIA_BUCKET_FOR_SYNC,  # sync from
            's3://%s' % settings.AWS_STORAGE_BUCKET_NAME,  # sync to
        ]  # syncs replica from origin
        aws_open(sync_s3)

        download_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            's3://%s/%s' % (
                settings.SYNC_BUCKET,  # bucket to pull from
                ntpath.basename(settings.SYNC_FIXTURE_LOCATION),  # filename
            ),
            settings.SYNC_FIXTURE_LOCATION,  # local temp filename
        ]  # command to pull down fixture to local file, with aws env vars
        aws_open(download_s3)
        run_sql('drop schema public cascade;')
        run_sql('create schema public;')
        pg_load(settings.SYNC_FIXTURE_LOCATION)
