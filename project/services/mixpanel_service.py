from mixpanel import Mixpanel
from . import logging_service
from django.conf import settings


_mixpanel_client = None


def get_mixpanel_client():
    # Why this? seems like there must be a simpler way
    global _mixpanel_client
    if _mixpanel_client is None:
        mixpanel_key = getattr(settings, 'MIXPANEL_KEY', None)
        if mixpanel_key:
            _mixpanel_client = Mixpanel(mixpanel_key)
    return _mixpanel_client
