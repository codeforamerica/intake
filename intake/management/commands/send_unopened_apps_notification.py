from django.core.management.base import BaseCommand

from django.conf import settings

from intake import notifications, models


class Command(BaseCommand):
    help = 'Sends an email about unopened applications'

    def handle(self, *args, **options):
        email = settings.DEFAULT_NOTIFICATION_EMAIL
        unopened_submissions = models.FormSubmission.get_unopened_apps()
        count = len(unopened_submissions)
        notifications.front_email_daily_app_bundle.send(
            to=email,
            count=count,
            submission_ids=[s.id for s in unopened_submissions]
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Email {} with a link to {} unopened applications".format(
                    email, count)
                )
            )
