from rest_framework import serializers
from intake import models, serializer_fields
from user_accounts.models import Organization


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApplicationEvent


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['slug', 'name']


class FormSubmissionSerializer(serializers.ModelSerializer):
    organizations = OrganizationSerializer(many=True)
    contact_preferences = serializer_fields.DictKeyField(
        'contact_preferences', source='answers')
    monthly_income = serializer_fields.DictKeyField(
        'monthly_income', source='answers')
    us_citizen = serializer_fields.YesNoAnswerField(
        'us_citizen', source='answers')
    being_charged = serializer_fields.YesNoAnswerField(
        'being_charged', source='answers')
    serving_sentence = serializer_fields.YesNoAnswerField(
        'serving_sentence', source='answers')
    on_probation_parole = serializer_fields.YesNoAnswerField(
        'on_probation_parole', source='answers')
    currently_employed = serializer_fields.YesNoAnswerField(
        'currently_employed', source='answers')
    city = serializer_fields.CityField(source='answers')
    age = serializer_fields.AgeField(source='answers')
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
            'url'
        ]


class ApplicantSerializer(serializers.ModelSerializer):
    started = serializer_fields.Started(source='events')
    finished = serializer_fields.Finished(source='events')
    had_errors = serializer_fields.HadErrors(source='events')
    ip = serializer_fields.IPAddress(source='events')
    referrer = serializer_fields.Referrer(source='events')
    events = ApplicationEventSerializer(many=True)
    form_submissions = FormSubmissionSerializer(many=True)

    class Meta:
        model = models.Applicant

    def to_representation(self, obj):
        data = super().to_representation(obj)
        subs = data.pop('form_submissions', [])
        sub_data = next(iter(subs), {})
        sub_data['submission_id'] = sub_data.pop('id', None)
        data.update(sub_data)
        return data
