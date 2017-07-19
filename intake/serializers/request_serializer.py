from django.conf import settings
from rest_framework import serializers
from .fields import ChainableAttributeField
from intake.constants import LANGUAGES_LOOKUP


class RequestSerializer(serializers.Serializer):
    visitor_source = ChainableAttributeField('visitor.source')
    visitor_referrer = ChainableAttributeField('visitor.referrer')
    path = ChainableAttributeField('path')
    full_path = serializers.SerializerMethodField(read_only=True)
    compact_user_agent = serializers.SerializerMethodField(read_only=True)
    browser_family = ChainableAttributeField('user_agent.browser.family')
    browser_version = ChainableAttributeField(
        'user_agent.browser.version_string')
    os_family = ChainableAttributeField('user_agent.os.family')
    os_version = ChainableAttributeField('user_agent.os.version_string')
    device_family = ChainableAttributeField('user_agent.device.family')
    device_brand = ChainableAttributeField('user_agent.device.brand')
    device_model = ChainableAttributeField('user_agent.device.model')
    is_mobile = ChainableAttributeField('user_agent.is_mobile')
    is_tablet = ChainableAttributeField('user_agent.is_tablet')
    is_touch_capable = ChainableAttributeField('user_agent.is_touch_capable')
    is_pc = ChainableAttributeField('user_agent.is_pc')
    is_bot = ChainableAttributeField('user_agent.is_bot')
    locale = ChainableAttributeField('LANGUAGE_CODE')
    language = serializers.SerializerMethodField(read_only=True)

    def get_compact_user_agent(self, request):
        return str(request.user_agent)

    def get_language(self, request):
        return LANGUAGES_LOOKUP.get(
            request.LANGUAGE_CODE, request.LANGUAGE_CODE)

    def get_full_path(self, request):
        return request.get_full_path()
