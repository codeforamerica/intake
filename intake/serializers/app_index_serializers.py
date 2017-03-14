from intake import models
from rest_framework import serializers
from . import fields
from .status_update_serializer import MinimalStatusUpdateSerializer
from .application_serializer import LatestStatusBase
from .application_transfer_serializer import IncomingTransferSerializer


class FormSubmissionIndexSerializer(serializers.ModelSerializer):
    local_date_received = fields.LocalDateField(source='date_received')
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = models.FormSubmission
        fields = [
            'id',
            'local_date_received',
            'full_name',
            'url',
            'phone_number',
            'email',
        ]


class ApplicationIndexSerializer(LatestStatusBase):
    form_submission = FormSubmissionIndexSerializer()
    status_updates = MinimalStatusUpdateSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'status_updates',
            'form_submission',
            'was_transferred_out'
        ]


class ApplicationIndexWithTransfersSerializer(ApplicationIndexSerializer):
    incoming_transfers = IncomingTransferSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'status_updates',
            'form_submission',
            'was_transferred_out',
            'incoming_transfers'
        ]
