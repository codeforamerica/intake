import os
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.staticfiles.management.commands import collectstatic


class Command(collectstatic.Command):

    def handle(self, *args, **options):
        new_font_path = os.path.join(settings.REPO_DIR,
                                        'intake/static/intake/fonts')
        if not os.path.exists(new_font_path):
            font_path = os.path.join(settings.NODE_MODULES_PATH,
                                     'bootstrap/fonts')
            os.symlink(font_path, new_font_path)
        super(Command, self).handle(*args, **options)
        call_command(
            'compress',
            engine="jinja2",
            extension=["jinja"],
            interactive=False,
        )
