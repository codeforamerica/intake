import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from urllib.parse import urljoin


URLS_SHOULD_200 = [
    '/',
    'apply/',
]


class Command(BaseCommand):
    help = str(
        "This should error if a url fails for a given domain.")

    def add_arguments(self, parser):
        parser.add_argument('domains', nargs='+', type=str)

    def handle(self, *args, **kwargs):
        for domain in kwargs['domains']:
            for path in URLS_SHOULD_200:
                url = urljoin(domain, path)
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception('%s returned a %s' % (url, r.status_code))
