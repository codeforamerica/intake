import json
import csv

from django.conf import settings
from django.core.management import BaseCommand
from requests import request


class Command(BaseCommand):
    help = str(
        "Scrapes logs for FRONT POST and sends messages."
        "This was created to recover from the scenario where "
        "DIVERT_REMOTE_CONNECTIONS was accidentally set to True on production")

    def handle(self, *args, **kwargs):
        FRONT_EMAIL_CHANNEL_ID = 'cha_ok0'
        FRONT_PHONE_CHANNEL_ID = 'cha_nx8'

        with open('./logs_temp/front_posts.tsv', 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter='\t')
            for row in spamreader:
                post = row[9][11:]
                post_json = json.loads(post)
                to_field = post_json['to'][0]

                is_email = '@' in to_field
                if is_email:
                    channel_id = FRONT_EMAIL_CHANNEL_ID
                else:
                    channel_id = FRONT_PHONE_CHANNEL_ID
                root_url = 'https://api2.frontapp.com/channels/{}/messages'\
                    .format(channel_id)
                print("Sending {} to {}".format(is_email, to_field))
                request(url=root_url,
                        data=post,
                        method='POST',
                        headers={
                            'Authorization': 'Bearer {}'.format(getattr(
                                settings, 'FRONT_API_TOKEN', None)),
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        })
