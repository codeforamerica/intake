from django.conf import settings
from mixpanel import Mixpanel
from . import logging_service


_mixpanel_client = None


def get_mixpanel_client():
    global _mixpanel_client
    if _mixpanel_client is None:
        mixpanel_key = getattr(settings, 'MIXPANEL_KEY', None)
        if mixpanel_key:
            _mixpanel_client = Mixpanel(mixpanel_key)
    return _mixpanel_client


def log_to_mixpanel(distinct_id, event_name, **data):
    client = get_mixpanel_client()
    divert = getattr(settings, 'DIVERT_REMOTE_CONNECTIONS', False)
    mixpanel_kwargs = dict(
            distinct_id=distinct_id,
            event_name=event_name,
            properties=data)
    if client and not divert:
        client.track(**mixpanel_kwargs)
    logging_service.format_and_log(
        log_type='call_to_mixpanel', **mixpanel_kwargs)
