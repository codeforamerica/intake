from intake import models
from rest_framework import serializers
from . import fields
from .status_update_serializer import MinimalStatusUpdateSerializer
from .application_serializers import LatestStatusBase
from .application_transfer_serializer import IncomingTransferSerializer


class FormSubmissionIndexSerializer(serializers.ModelSerializer):
    local_date_received = fields.LocalDateField(source='date_received')
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    printout_url = serializers.CharField(
        source='get_case_printout_url', read_only=True)

    class Meta:
        model = models.FormSubmission
        fields = [
            'id',
            'local_date_received',
            'first_name',
            'last_name',
            'url',
            'printout_url',
            'phone_number',
            'email',
        ]


class ApplicationIndexSerializer(LatestStatusBase):
    local_created = fields.LocalDateField(source='created')
    form_submission = FormSubmissionIndexSerializer()
    status_updates = MinimalStatusUpdateSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'local_created',
            'status_updates',
            'form_submission',
            'was_transferred_out',
            'has_been_opened'
        ]


class ApplicationIndexWithTransfersSerializer(ApplicationIndexSerializer):
    incoming_transfers = IncomingTransferSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'local_created',
            'status_updates',
            'form_submission',
            'was_transferred_out',
            'incoming_transfers',
            'has_been_opened'
        ]
