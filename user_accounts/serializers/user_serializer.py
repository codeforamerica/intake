from rest_framework import serializers
from intake.serializers.fields import ChainableAttributeField


class UserMixpanelSerializer(serializers.Serializer):
    """This serializes user information from a user instance
    """
    user_organization_name = ChainableAttributeField(
        'profile.organization.name')
    user_username = ChainableAttributeField('username')
