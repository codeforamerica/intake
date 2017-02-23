from celery import shared_task
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


@shared_task
def mixpanel_task(distinct_id, event_name, data):
    client = get_mixpanel_client()
    if client:
        client.track(
            distinct_id=distinct_id,
            event_name=event_name,
            properties=data)
