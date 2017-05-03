import os
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.staticfiles.management.commands import collectstatic


class Command(collectstatic.Command):

    def handle(self, *args, **options):
        sass = settings.COMPRESS_PRECOMPILERS[0][1]
        from subprocess import Popen
        command = sass.format(
            infile='intake/static/intake/scss/main.scss',
            outfile='out.css')
        print(command)
        Popen(command, shell=True)
        Popen('ls', shell=True)
        Popen('env', shell=True)
        super(Command, self).handle(*args, **options)
        call_command(
            'compress',
            engine="jinja2",
            extension=["jinja"],
            interactive=False,
        )
