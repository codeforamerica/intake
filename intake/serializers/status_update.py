from rest_framework import serializers
from intake import models


class StatusUpdateSerializer(serializers.ModelSerializer):
    status_type = serializers.SlugRelatedField(
        read_only=True, slug_field='display_name')
    next_steps = serializers.SlugRelatedField(
        read_only=True, many=True, slug_field='display_name')

    class Meta:
        model = models.StatusUpdate
        fields = [
            'status_type',
            'next_steps',
            'updated'
        ]
