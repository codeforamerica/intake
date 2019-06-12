from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from intake.models import Application
from project.alerts import send_email_to_admins
from user_accounts.models import Organization


class Command(BaseCommand):
    help = str(
        "Check if any organizations have unread applications "
        "older than 30 days")

    def handle(self, *args, **kwargs):
        now = timezone.now()
        oldest_allowed_submission_date = now - timedelta(days=30)
        for org in Organization.objects.all():
            latest_login = User.objects.filter(
                profile__organization__id=org.id,
                profile__organization__is_live=True,
                last_login__isnull=False
            ).values_list('last_login', flat=True).first()

            if not latest_login:
                continue

            unread_applications = Application.objects.filter(
                has_been_opened=False,
                was_transferred_out=False,
                organization__id=org.id)
            unread_applications_count = unread_applications.count()

            if unread_applications_count <= 0:
                continue

            submission_dates = [
                app.form_submission.get_local_date_received()
                for app in unread_applications
            ]
            oldest_submission_date = min(submission_dates)

            if oldest_submission_date >= oldest_allowed_submission_date:
                continue

            subject = "Inactive organization on {}".format(
                settings.DEFAULT_HOST)
            msg = "{} has {} unopened applications, the oldest from" \
                  " {}. We should contact them.".format(
                        org.name, unread_applications_count,
                        oldest_submission_date.strftime('%-m/%-d/%y'))
            print(msg)
            send_email_to_admins(subject=subject, message=msg)
