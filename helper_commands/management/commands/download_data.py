
class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Downloads from s3 and loads data.")

    def handle(self, *args, **kwargs):
        sync_s3 = [
            's3', 'sync'
            's3://%' % settings.ORIGIN_MEDIA_BUCKET_FOR_SYNC,
            's3://%' % settings.AWS_STORAGE_BUCKET_NAME,
        ]
        aws_open(sync_s3)
        download_s3 = [
            settings.AWS_CLI_LOCATION,
            's3', 'mv',
            's3://%s' % settings.SYNC_BUCKET,
            settings.SYNC_FIXTURE_LOCATION,
        ]
        aws_open(download_s3)
        call_command('flush', interactive=False)
        management.call_command('loaddata', settings.SYNC_FIXTURE_LOCATION)
