from intake import models
from rest_framework import serializers
from .fields import LocalDateField
from .application_transfer_serializer import IncomingTransferSerializer


class MinimalStatusUpdateSerializer(serializers.ModelSerializer):
    created = LocalDateField()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')

    class Meta:
        model = models.StatusUpdate
        fields = [
            'created',
            'status_type',
        ]


class StatusNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.StatusNotification
        fields = [
            'sent_message',
            'contact_info'
        ]


class StatusUpdateSerializer(serializers.ModelSerializer):
    created = LocalDateField()
    notification = StatusNotificationSerializer()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')
    next_steps = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name', many=True)
    author_name = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()
    transfer = serializers.SerializerMethodField()

    class Meta:
        model = models.StatusUpdate
        fields = [
            'id',
            'created',
            'notification',
            'status_type',
            'additional_information',
            'next_steps',
            'other_next_step',
            'organization_name',
            'author_name',
            'transfer'
        ]

    def get_author_name(self, instance):
        return instance.author.profile.name

    def get_organization_name(self, instance):
        return instance.author.profile.organization.name

    def get_transfer(self, instance):
        # this prevents us from querying for a transfer unless it exists
        if instance.status_type.slug == 'transferred':
            return IncomingTransferSerializer().to_representation(
                instance.transfer)
        return None


class StatusUpdateCSVDownloadSerializer(serializers.ModelSerializer):
    created = LocalDateField()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')
    author_email = serializers.SerializerMethodField()

    def get_author_email(self, instance):
        return instance.author.email

    class Meta:
        model = models.StatusUpdate
        fields = [
            'created',
            'status_type',
            'author_email',
        ]
