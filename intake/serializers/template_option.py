from rest_framework import serializers
from intake import models


class StatusTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.StatusType
        fields = ['slug', 'display_name']


class NextStepSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.NextStep
        fields = ['slug', 'display_name']
