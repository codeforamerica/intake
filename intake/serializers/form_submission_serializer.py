from . import fields
from rest_framework import serializers
from intake import models
from .application_serializers import ApplicationFollowupListSerializer
from .note_serializer import ApplicationNoteSerializer
from .tag_serializer import TagSerializer


class FormSubmissionFollowupListSerializer(serializers.ModelSerializer):
    local_date_received = fields.LocalDateField(source='date_received')
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    applications = ApplicationFollowupListSerializer(many=True)
    notes = ApplicationNoteSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = models.FormSubmission
        fields = [
            'id',
            'local_date_received',
            'full_name',
            'url',
            'phone_number',
            'email',
            'applications',
            'notes',
            'tags'
        ]
