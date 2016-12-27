from rest_framework import serializers
from django.contrib.auth.models import User
from intake import models
from intake.serializers.fields import (LocalDateField, )


class ApplicationNoteSerializer(serializers.ModelSerializer):
    created = LocalDateField(format='%b %-d', required=False)
    submission = serializers.PrimaryKeyRelatedField(
        queryset=models.FormSubmission.objects.all())
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True))

    class Meta:
        model = models.ApplicationNote
        fields = [
            'id',
            'submission',
            'body',
            'created',
            'user'
        ]

    def to_representation(self, obj):
        name = obj.user.first_name
        base = super().to_representation(obj)
        base['user'] = name
        return base
