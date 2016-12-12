from . import fields
from rest_framework import serializers
from intake import models
from user_accounts.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['slug', 'name']


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


class FollowupInfoSerializer(serializers.ModelSerializer):
    organizations = serializers.SlugRelatedField(
        many=True, slug_field='slug', read_only=True)
    date_received = fields.LocalDateField()
    first_name = fields.DictKeyField('first_name', source='answers')
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    where_they_heard = fields.DictKeyField(
        'how_did_you_hear', source='answers')
    contact_preferences = fields.DictKeyField(
        'contact_preferences', source='answers')
    being_charged = fields.YesNoAnswerField('being_charged', source='answers')
    serving_sentence = fields.YesNoAnswerField(
        'serving_sentence', source='answers')
    us_citizen = fields.YesNoAnswerField('us_citizen', source='answers')
    is_duplicate = fields.TruthyValueField(source='duplicate_set_id')
    contact_info = fields.ContactInfoByPreferenceField(source='answers')
    additional_info = fields.DictKeyField(
        'additional_information', source='answers')
    # not yet implemented:
    #   # missing_or_invalid_fields =
    #   # has_a_lot_of_probation_left =

    class Meta:
        model = models.FormSubmission
        fields = [
            'id',
            'date_received',
            'organizations',
            'contact_preferences',
            'first_name',
            'url',
            'where_they_heard',
            'additional_info',
            'being_charged',
            'serving_sentence',
            'us_citizen',
            'is_duplicate',
            'contact_info',
        ]
