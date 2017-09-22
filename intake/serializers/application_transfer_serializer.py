from intake import models
from rest_framework import serializers
from . import fields


class IncomingTransferSerializer(serializers.ModelSerializer):
    organization_name = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    local_date = serializers.SerializerMethodField()
    to_organization_name = serializers.SerializerMethodField()

    class Meta:
        model = models.ApplicationTransfer
        fields = [
            'to_organization_name',
            'organization_name',
            'author_name',
            'local_date',
            'reason'
        ]

    def get_to_organization_name(self, instance):
        return instance.new_application.organization.name

    def get_organization_name(self, instance):
        return instance.status_update.application.organization.name

    def get_author_name(self, instance):
        return instance.status_update.author.profile.name

    def get_local_date(self, instance):
        return fields.LocalDateField().to_representation(
            instance.status_update.created)
