from . import fields
from rest_framework import serializers
from intake import models
from .form_submission_serializer import FormSubmissionSerializer
from intake.constants import PACIFIC_TIME


class ApplicationEventSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    def get_time(self, event):
        return event.time.astimezone(PACIFIC_TIME)

    class Meta:
        model = models.ApplicationEvent
        fields = ['id', 'name', 'time', 'data']


class ApplicantSerializer(serializers.ModelSerializer):
    started = fields.Started()
    finished = fields.Finished()
    had_errors = fields.HadErrors()
    ip = fields.IPAddress()
    referrer = fields.Referrer()
    events = ApplicationEventSerializer(many=True)
    form_submissions = FormSubmissionSerializer(many=True)
    tried_to_apply = serializers.SerializerMethodField(
        method_name='check_if_they_actually_tried_to_apply')
    is_multicounty = serializers.SerializerMethodField(
        method_name='check_if_they_are_multicounty')

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
            'tried_to_apply',
            'is_multicounty',
            'visitor_id'
        ]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        subs = data.pop('form_submissions', [])
        sub_data = next(iter(subs), {})
        sub_data['submission_id'] = sub_data.pop('id', None)
        data.update(sub_data)
        return data

    def check_if_they_actually_tried_to_apply(self, obj):
        return fields.made_a_meaningful_attempt_to_apply(obj)

    def check_if_they_are_multicounty(self, obj):
        return fields.is_multicounty(obj)
