from intake import models
from rest_framework import serializers
from .status_update import MinimalStatusUpdateSerializer


class ApplicationFollowupListSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        read_only=True, slug_field='slug')
    status_updates = MinimalStatusUpdateSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'organization',
            'status_updates'
        ]

    def to_representation(self, *args, **kwargs):
        data = super().to_representation(*args, **kwargs)
        sorted_status_updates = sorted(
            data.get('status_updates', []), key=lambda d: d['updated'],
            reverse=True)
        latest_status = \
            sorted_status_updates[0] if sorted_status_updates else None
        data.update(latest_status=latest_status)
        return data
