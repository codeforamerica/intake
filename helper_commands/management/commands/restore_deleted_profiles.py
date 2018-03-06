import json

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from easyaudit.models import CRUDEvent

from user_accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Reads deleted profiles from the audit log table and restores them'

    def handle(self, *args, **kwargs):
        user_profile_type = ContentType.objects.filter(
            app_label='user_accounts', model='userprofile')

        deleted_profiles = CRUDEvent.objects.filter(
            content_type=user_profile_type, event_type=CRUDEvent.DELETE)

        for profile_log in deleted_profiles:
            print("Restoring", profile_log.object_repr, "...")

            profile = json.loads(profile_log.object_json_repr)[0]
            fields = profile['fields']
            user_id = fields.pop('user')
            org_id = fields.pop('organization')
            fields['user_id'] = user_id
            fields['organization_id'] = org_id
            fields['should_get_notifications'] = False
            UserProfile.objects.create(**fields)

