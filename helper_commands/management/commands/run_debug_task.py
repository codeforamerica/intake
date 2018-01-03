from django.core.management.base import BaseCommand
from intake.tasks import debug_task


class Command(BaseCommand):
    help = str(
        "[THIS IS NOT FOR USE ON PERSONAL MACHINES]"
        "Downloads from s3 and loads data.")

    def handle(self, *args, **kwargs):
        debug_task('test single arguement')
