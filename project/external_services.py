from django.conf import settings


def log_to_mixpanel(user_id, event_name, data):
    divert = getattr(settings, 'DIVERT_REMOTE_CONNECTIONS', False)
    if not divert:
        from intake.tasks import mixpanel_task
        mixpanel_task.delay(user_id, event_name, data)
