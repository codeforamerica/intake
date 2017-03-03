from . import fields
from rest_framework import serializers
from intake import models
from .organization_serializer import OrganizationSerializer
from .application_serializer import ApplicationFollowupListSerializer
from .note_serializer import ApplicationNoteSerializer
from .tag_serializer import TagSerializer


class FormSubmissionSerializer(serializers.ModelSerializer):
    organizations = OrganizationSerializer(many=True)
    contact_preferences = fields.DictKeyField(
        'contact_preferences', source='answers')
    monthly_income = fields.DictKeyField(
        'monthly_income', source='answers')
    us_citizen = fields.YesNoAnswerField(
        'us_citizen', source='answers')
    being_charged = fields.YesNoAnswerField(
        'being_charged', source='answers')
    serving_sentence = fields.YesNoAnswerField(
        'serving_sentence', source='answers')
    on_probation_parole = fields.YesNoAnswerField(
        'on_probation_parole', source='answers')
    currently_employed = fields.YesNoAnswerField(
        'currently_employed', source='answers')
    city = fields.CityField(source='answers')
    age = fields.AgeField(source='answers')
    where_they_heard = fields.DictKeyField(
        'how_did_you_hear', source='answers')
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = models.FormSubmission
        fields = [
            'id',
            'date_received',
            'organizations',
            'contact_preferences',
            'monthly_income',
            'us_citizen',
            'being_charged',
            'serving_sentence',
            'on_probation_parole',
            'currently_employed',
            'city',
            'age',
            'url',
            'where_they_heard'
        ]


class FormSubmissionFollowupListSerializer(serializers.ModelSerializer):
    local_date_received = fields.LocalDateField(source='date_received')
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    phone_number = fields.DictKeyField('phone_number', source='answers')
    email = fields.DictKeyField('email', source='answers')
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
