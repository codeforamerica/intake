from rest_framework import serializers
from intake import aggregate_serializer_fields as agg_fields


class PublicDaySerializer(serializers.Serializer):
    count = agg_fields.FinishedCountField(
        source='applications_today')
    weekly_total = agg_fields.FinishedCountField(
        source='applications_this_week')
    weekly_mean_completion_time = agg_fields.MeanCompletionTimeField(
        source='applications_this_week')
    weekly_median_completion_time = agg_fields.MedianCompletionTimeField(
        source='applications_this_week')


class PrivateDaySerializer(PublicDaySerializer):
    referrers = agg_fields.MajorSourcesField(
        source='applications_this_week')
    weekly_dropoff_rate = agg_fields.DropOffField(
        source='applications_this_week')
