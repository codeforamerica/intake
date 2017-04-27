from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.staticfiles.management.commands import collectstatic


class Command(collectstatic.Command):

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
        from django.conf import settings
        print(settings.STATIC_ROOT)
        print(settings.DEFAULT_FILE_STORAGE)
        print(settings.STATICFILES_STORAGE)
        from subprocess import Popen
        Popen('find /  -name "stats_entry.js"', shell=True)
        call_command('compress',
                     engine="jinja2", extension=["jinja"], interactive=False)
