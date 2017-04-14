import time
from django.db import connections
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings
from subprocess import Popen


class Command(BaseCommand):
    help = str(
        "This should fail is something is broken. Hopefully ;)")

    def handle(self, *args, **kwargs):
        # Check db connect works
        db_conn = connections['default']
        c = db_conn.cursor()  # If broken this will fail
        # Check celery works exist
        from celery.task.control import inspect
        insp = inspect()
        celery_worker_stats = insp.stats()
        if not celery_worker_stats:
            raise Exception("No Celery Workers")
        """
        wsgi = Popen('./manage.py runserver', shell=True)
        time.sleep(3)
        management.call_command('test_urls_200', 'http://localhost:8000')
        wsgi.kill()
        wsgi.wait()
        """
