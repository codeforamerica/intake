from rest_framework import serializers
from .fields import ChainableAttributeField
from intake.constants import LANGUAGES_LOOKUP


class ViewMixpanelSerializer(serializers.Serializer):
    view_name = ChainableAttributeField('__class__.__name__')
