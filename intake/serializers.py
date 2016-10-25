from rest_framework import serializers
from intake import models, serializer_fields
from user_accounts.models import Organization


class ApplicationEventSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    def get_time(self, event):
        return event.time.astimezone(serializer_fields.PACIFIC).isoformat()

    class Meta:
        model = models.ApplicationEvent
        fields = ['time', 'name', 'data']


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
    started = serializer_fields.Started()
    finished = serializer_fields.Finished()
    had_errors = serializer_fields.HadErrors()
    ip = serializer_fields.IPAddress()
    referrer = serializer_fields.Referrer()
    events = ApplicationEventSerializer(many=True)
    form_submissions = FormSubmissionSerializer(many=True)
    tried_to_apply = serializers.SerializerMethodField(
        method_name='check_if_they_actually_tried_to_apply')

    class Meta:
        model = models.Applicant
        fields = [
            'id',
            'started',
            'finished',
            'had_errors',
            'ip',
            'referrer',
            'events',
            'form_submissions',
            'tried_to_apply'
        ]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        subs = data.pop('form_submissions', [])
        sub_data = next(iter(subs), {})
        sub_data['submission_id'] = sub_data.pop('id', None)
        data.update(sub_data)
        return data

    def check_if_they_actually_tried_to_apply(self, obj):
        return serializer_fields.made_a_meaningful_attempt_to_apply(obj)
