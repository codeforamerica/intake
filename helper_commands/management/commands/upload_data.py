from subprocess import Popen
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Dumps database and uploads to s3")

    def handle(self, *args, **kwargs):
        with open(settings.SYNC_FIXTURE_LOCATION, 'w+') as f:
            management.call_command('dumpdata', stdout=f)
        upload_command = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            settings.SYNC_FIXTURE_LOCATION,
            's3://%s' % settings.SYNC_BUCKET,
        ]
        Popen(upload_command, env={
            "AWS_ACCESS_KEY_ID": settings.SYNC_AWS_ID,
            "AWS_SECRET_ACCESS_KEY": settings.SYNC_AWS_KEY,
        })
