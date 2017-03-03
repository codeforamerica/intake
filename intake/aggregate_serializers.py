from rest_framework import serializers
from intake import aggregate_serializer_fields as fields


class PublicStatsSerializer(serializers.Serializer):
    total = fields.FinishedCountField(source='apps')
    weekly_totals = fields.WeeklyTotals(source='apps')
    apps_this_week = fields.AppsThisWeek(source='apps')
    mean_completion_time = serializers.SerializerMethodField(
        method_name='get_scoped_mean_time')
    median_completion_time = serializers.SerializerMethodField(
        method_name='get_scoped_median_time')

    def get_scoped_mean_time(self, data):
        return fields.MeanCompletionTimeField(
        ).to_representation(data['apps'], data['org'])

    def get_scoped_median_time(self, data):
        return fields.MedianCompletionTimeField(
        ).to_representation(data['apps'], data['org'])


class PrivateStatsSerializer(PublicStatsSerializer):
    channels = fields.Channels(source='apps')
    drop_off = fields.DropOff(source='apps')
    app_error_rate = fields.ErrorRate(source='apps')
    where_they_heard = fields.WhereTheyHeard(source='apps')


# class ExtraStatsSerializer(PrivateStatsSerializer):
#     income_brackets = fields.IncomeBrackets()
#     age_brackets = fields.AgeBrackets()
#     multicounty = fields.MultiCounty()
#     common_errors = fields.CommonErrors()
#     dropoff_errors = fields.DropOffErrors()
#     common_ips = fields.CommonIPs()
#     where_they_heard = fields.WhereTheyHeard()
