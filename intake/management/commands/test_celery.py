from django.core import management
from django.core.management.base import BaseCommand

from project import celery
from django.conf import settings


class Command(BaseCommand):
    help = str(
        "Sets up seeds based on what environment it runs in.")

    def handle(self, *args, **kwargs):
        print(settings)
        print(settings.CELERY_TASK_ALWAYS_EAGER)
        celery.debug_task.delay()
