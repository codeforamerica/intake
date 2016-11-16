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


"""
Each field should be responsible for defining the window and scope

PublicStatsSerializer(serializers.Serializer):
    total = agg_fields.FinishedCountField()
    daily_totals = agg_fields.DailyTotals()
    apps_this_week = agg_fields.WeeklyTotal()
    mean_completion_time = agg_fields.MeanCompletionTimeField()
    median_completion_time = agg_fields.MedianCompletionTimeField()


PrivateStatsSerializer(PublicStatsSerializer):
    channels = agg_fields.Channels()
    drop_off = agg_fields.DropOff()
    app_error_rate = agg_fields.ChannelsField()


ExtraStatsSerializer(PrivateStatsSerializer):
    income_brackets = agg_fields.IncomeBrackets()
    age_brackets = agg_fields.AgeBrackets()
    multicounty = agg_fields.MultiCounty()
    common_errors = agg_fields.CommonErrors()
    dropoff_errors = agg_fields.DropOffErrors()
    common_ips = agg_fields.CommonIPs()
    where_they_heard = agg_fields.WhereTheyHeard()

"""
