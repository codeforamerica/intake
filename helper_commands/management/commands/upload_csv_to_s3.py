import csv
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from django.conf import settings
from django.core.management.base import BaseCommand
from intake.models import FormSubmission


class Command(BaseCommand):
    help = 'Exfiltrates data to s3.  Please dont abuse'

    def handle(self, *args, **kwargs):
        filename = '/tmp/database_export.csv'
        with open(filename, 'w') as csvfile:
            writer = csv.writer(
                csvfile,
                delimiter='\t',
                quoting=csv.QUOTE_MINIMAL)
            headers = [
                'ID',
                'Submission date',
                'Email',
                'Phone number',
                'Prefers Email',
                'Prefers SMS',
                'Counties',
                'How did you hear',
                'Anything else we should know',
                'Last Status Update At',
                'Last Status',
                'Is Eligible',
                'Is Granted',
                'Notes',
                'Tags'
            ]

            writer.writerow(headers)

            subs = FormSubmission.objects.order_by('id').all()
            for sub in subs:
                for app in sub.applications.all():
                    granted = app.status_updates.filter(
                        status_type__slug='granted').count() > 0

                    eligible = app.status_updates.filter(
                        status_type__slug='eligible').count() > 0

                    last_status = app.status_updates.order_by(
                        '-updated').first()
                    if last_status:
                        last_status_name = last_status.status_type.display_name
                        last_status_date = last_status.updated.strftime(
                            "%Y-%m-%d")
                    else:
                        last_status_name = None
                        last_status_date = None

                    columns = [
                        sub.id,
                        sub.date_received.strftime("%Y-%m-%d"),
                        sub.email,
                        sub.phone_number,
                        'prefers_email' in sub.contact_preferences,
                        'prefers_sms' in sub.contact_preferences,
                        app.organization.name,
                        sub.how_did_you_hear,
                        sub.additional_information,
                        last_status_date,
                        last_status_name,
                        eligible,
                        granted
                    ]

                    writer.writerow(columns)
            conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                                settings.AWS_SECRET_ACCESS_KEY)
            media_bucket = conn.get_bucket(settings.MEDIA_BUCKET)
            key = Key(media_bucket)
            key.key = 'database_export.csv'
            key.set_contents_from_filename(filename)
