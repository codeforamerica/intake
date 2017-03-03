from intake import models
from rest_framework import serializers
from .fields import LocalDateField


class MinimalStatusUpdateSerializer(serializers.ModelSerializer):
    updated = LocalDateField()
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')
    next_steps = serializers.SlugRelatedField(
        read_only=True, many=True, slug_field='display_name')

    class Meta:
        model = models.StatusUpdate
        fields = [
            'updated',
            'status_type',
            'next_steps'
        ]
