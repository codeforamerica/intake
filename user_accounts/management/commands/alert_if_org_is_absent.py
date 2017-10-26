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
        "Check if any organizations have not logged in for the past 20 days")

    def handle(self, *args, **kwargs):
        now = timezone.now()
        oldest_allowed_login_date = now - timedelta(days=20)
        for org in Organization.objects.all():
            latest_login = User.objects.filter(
                profile__organization__id=org.id,
                profile__organization__is_live=True,
                last_login__isnull=False
            ).order_by("-last_login").values_list(
                'last_login', flat=True).first()

            if latest_login and (latest_login < oldest_allowed_login_date):
                latest_login_string = latest_login.strftime("%a %b %-d %Y")

                unread_applications_count = Application.objects.filter(
                    has_been_opened=False, organization__id=org.id).count()
                subject = "Inactive organization on {}".format(
                    settings.DEFAULT_HOST)
                msg = "{} has not logged in since {} and has {} unopened " \
                      "applications. We should contact them.".format(
                        org.name, latest_login_string,
                        unread_applications_count)
                if unread_applications_count > 0:
                    send_email_to_admins(subject=subject, message=msg)
