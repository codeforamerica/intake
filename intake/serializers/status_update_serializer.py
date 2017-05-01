from intake import models
import Levenshtein
from rest_framework import serializers
from .fields import LocalDateField, FormattedLocalDateField
from .application_transfer_serializer import IncomingTransferSerializer
from intake.services import status_notifications as StatusNotificationsService


class MinimalStatusUpdateSerializer(serializers.ModelSerializer):
    updated = LocalDateField()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')

    class Meta:
        model = models.StatusUpdate
        fields = [
            'updated',
            'status_type',
        ]


class StatusNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.StatusNotification
        fields = [
            'sent_message',
            'contact_info'
        ]


class StatusNotificationAnalysisSerializer(serializers.ModelSerializer):
    contact_info = serializers.SerializerMethodField()
    message_change = serializers.SerializerMethodField()
    was_edited = serializers.SerializerMethodField()

    class Meta:
        model = models.StatusNotification
        fields = [
            'contact_info',
            'message_change',
            'was_edited'
        ]

    def get_contact_info(self, notification):
        return list(notification.contact_info.keys())

    def get_message_change(self, notification):
        author_profile = notification.status_update.author.profile
        intro_text = StatusNotificationsService.get_notification_intro(
            author_profile) + '\n\n'
        return 1.0 - Levenshtein.ratio(
            *[message.replace(intro_text, '')
              for message in (
                notification.base_message, notification.sent_message)])

    def get_was_edited(self, notification):
        return notification.base_message != notification.sent_message


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
        if instance.status_type.id == models.status_type.TRANSFERRED:
            return IncomingTransferSerializer().to_representation(
                instance.transfer)
        return None


class StatusUpdateAnalysisSerializer(serializers.ModelSerializer):
    created = FormattedLocalDateField(format="%Y-%m-%d")
    notification = StatusNotificationAnalysisSerializer()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')
    next_steps = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name', many=True)
    organization_name = serializers.SerializerMethodField()
    additional_information_length = serializers.SerializerMethodField()
    additional_information_in_sent_message = \
        serializers.SerializerMethodField()
    other_next_step_length = serializers.SerializerMethodField()
    other_next_step_in_sent_message = serializers.SerializerMethodField()

    class Meta:
        model = models.StatusUpdate
        fields = [
            'id',
            'created',
            'notification',
            'status_type',
            'next_steps',
            'organization_name',
            'additional_information_length',
            'additional_information_in_sent_message',
            'other_next_step_length',
            'other_next_step_in_sent_message'
        ]

    def get_organization_name(self, instance):
        return instance.author.profile.organization.name

    def get_additional_information_length(self, instance):
        return len(instance.additional_information)

    def get_additional_information_in_sent_message(self, instance):
        notification = getattr(instance, 'notification', None)
        if notification and instance.additional_information:
            return (instance.additional_information in
                    instance.notification.sent_message)

    def get_other_next_step_length(self, instance):
        return len(instance.other_next_step)

    def get_other_next_step_in_sent_message(self, instance):
        notification = getattr(instance, 'notification', None)
        if notification and instance.other_next_step:
            return (instance.other_next_step in
                    instance.notification.sent_message)
