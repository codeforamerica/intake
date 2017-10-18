from django.core.management.base import BaseCommand

from user_accounts.models import UserProfile
from intake.services.mailgun_api_service import set_route_for_user_profile


class Command(BaseCommand):
    help = 'Creates Mailgun routes for each user profile'

    def handle(self, *args, **options):
        self.stdout.write('Sending route creation commands to Mailgun')
        for profile in UserProfile.objects.order_by('organization__slug'):
            set_route_for_user_profile(profile)
            message = '\t{} --> {}'.format(
                profile.get_clearmyrecord_email(),
                profile.user.email
            )
            self.stdout.write(message)
