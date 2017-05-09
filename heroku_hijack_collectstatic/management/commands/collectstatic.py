import os
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.staticfiles.management.commands import collectstatic


class Command(collectstatic.Command):

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
        call_command(
            'compress',
            engine="jinja2",
            extension=["jinja"],
            interactive=False,
        )
