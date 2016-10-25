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
