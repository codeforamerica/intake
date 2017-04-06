from django.conf import settings
from mixpanel import Mixpanel


_mixpanel_client = None


def get_mixpanel_client():
    global _mixpanel_client
    if _mixpanel_client is None:
        mixpanel_key = getattr(settings, 'MIXPANEL_KEY', None)
        if mixpanel_key:
            _mixpanel_client = Mixpanel(mixpanel_key)
    return _mixpanel_client


def log_to_mixpanel(user_uuid, event_name, data):
    client = get_mixpanel_client()
    divert = getattr(settings, 'DIVERT_REMOTE_CONNECTIONS', False)
    if client and not divert:
        client.track(
            distinct_id=user_uuid,
            event_name=event_name,
            properties=data)
