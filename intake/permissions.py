from django.contrib.auth.models import Permission

# apps
CAN_SEE_APP_STATS = 'view_app_stats'
CAN_SEE_APP_DETAILS = 'view_app_details'

# notes
CAN_SEE_FOLLOWUP_NOTES = 'view_application_note'


def get_all_followup_permissions():
    return Permission.objects.filter(
        codename__in=[
            CAN_SEE_FOLLOWUP_NOTES,
            'add_applicationnote',
            'delete_applicationnote'])
