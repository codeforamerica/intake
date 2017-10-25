from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from project.alerts import send_email_to_admins
from user_accounts.models import Organization


class Command(BaseCommand):
    help = str(
        "Check if any organizations have not logged in for the past 20 days")

    def handle(self, *args, **kwargs):
        now = timezone.now()
        oldest_allowed_login_date = now - timedelta(days=20)
        for org in Organization.objects.all():
            last_logins = User.objects.filter(
                profile__organization__id=org.id
            ).values_list('last_login', flat=True)
            last_logins = [
                login_datetime for login_datetime in last_logins
                if login_datetime != None
            ]
            if last_logins:
                latest_login = max(last_logins)
                no_recent_logins = latest_login < oldest_allowed_login_date
                latest_login_string = latest_login.strftime("%a %b %-d %Y")
            else:
                no_recent_logins = True
                latest_login_string = 'forever'
            unread_applications_count = Application.objects.filter(
                has_been_opened=False, organization__id=org.id).count()
            has_unread_applications = unread_applications_count > 0
            msg = "{} has not logged in since {} and has {} unopened " \
                  "applications".format(
                org.name, latest_login_string, unread_applications_count)
            if no_recent_logins and has_unread_applications:
                send_email_to_admins(
                    subject=msg, body="We should contact them")
