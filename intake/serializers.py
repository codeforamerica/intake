from rest_framework import serializers
from intake import models


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApplicationEvent


class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FormSubmission


class ApplicantSerializer(serializers.ModelSerializer):
    events = ApplicationEventSerializer(many=True)
    form_submissions = FormSubmissionSerializer(many=True)

    class Meta:
        model = models.Applicant