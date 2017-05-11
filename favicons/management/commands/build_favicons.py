from os import path
from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings
from subprocess import Popen


class Command(BaseCommand):
    help = str(
        "Builds favicons")

    def handle(self, *args, **kwargs):
        favicon_types = {
            'apple-touch-icon': (
                (57, 57),
                (60, 60),
                (72, 72),
                (76, 76),
                (114, 114),
                (120, 120),
                (144, 144),
                (152, 152),
                (180, 180),
            ),
            'icon': (
                (192, 192),
                (32, 32),
                (96, 96),
                (16, 16),
            ),
            'ms-icon': (
                (144, 144),
            ),
            'android-icon': (
                (36, 36),
                (48, 48),
                (72, 72),
                (96, 96),
                (144, 144),
                (192, 192),
            ),
            'ms-icon': (
                (70, 70),
                (150, 150),
                (310, 310),
            )
        }
        svg = './favicons/favicon.svg'
        cmd = "inkscape {svg} -h {h} -w {w} --export-png={path}"
        for key, value in favicon_types.items():
            for h, w in value:
                name = '%s-%sx%s.png' % (key, h, w)
                folder = path.join(
                    settings.REPO_DIR,
                    'favicons/static/favicons')
                png = path.join(folder, name)
                exe = cmd.format(svg=svg, h=h, w=w, path=png)
                Popen(exe, shell=True)
