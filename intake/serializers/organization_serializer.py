from rest_framework import serializers
from user_accounts.models import Organization


class OrganizationFollowupSerializer(serializers.ModelSerializer):
    county = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Organization
        fields = [
            'slug', 'name', 'county',
            'short_followup_message',
            'long_followup_message']


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ['slug', 'name', 'is_live']
