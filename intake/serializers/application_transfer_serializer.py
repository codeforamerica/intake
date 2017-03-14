from intake import models
from rest_framework import serializers
from . import fields


class IncomingTransferSerializer(serializers.ModelSerializer):
    organization_name = serializers.SerializerMethodField(
        method_name='get_organization_name')
    author_name = serializers.SerializerMethodField(
        method_name='get_author_name')
    local_date = serializers.SerializerMethodField(
        method_name='get_transfer_date')

    class Meta:
        model = models.ApplicationTransfer
        fields = [
            'organization_name',
            'author_name',
            'local_date',
            'reason'
        ]

    def get_organization_name(self, instance):
        return instance.organization.name

    def get_author_name(self, instance):
        return instance.status_update.author.profile.name

    def get_transfer_date(self, instance):
        return fields.LocalDateField().to_representation(
            instance.status_update.updated)
