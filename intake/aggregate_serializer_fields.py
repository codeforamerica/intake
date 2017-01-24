import statistics
import datetime
import urllib
import collections
from django.db import connection
from rest_framework import serializers
from intake import constants
from intake.utils import get_todays_date


def parse_url_host(full_url):
    if full_url:
        return urllib.parse.urlparse(full_url).netloc
    else:
        return ''


def parse_self_reported_referral(text):
    return text.lower()


def get_duration(start, end):
    tdelta = end - start
    return tdelta.total_seconds()


def seconds_to_complete(apps):
    durations = [
            get_duration(app['started'], app['finished'])
            for app in apps]
    return durations


def truthy_values_filter(apps, *keys):
    for app in apps:
        if all([app.get(key) for key in keys]):
            yield app


def single_org_filter(apps, org):
    all_orgs = org['slug'] == constants.Organizations.ALL
    for app in apps:
        if all_orgs:
            yield app
        else:
            orgs = app.get('organizations', [])
            if (len(orgs) == 1) and (orgs[0]['slug'] == org['slug']):
                yield app


class ApplicationAggregateField(serializers.Field):
    reducer = len

    def get_default_value(self):
        return None

    def filter(self, applications):
        return applications

    def reduce(self, applications):
        return self.reducer(applications)

    def to_representation(self, *args):
        filtered = self.filter(*args)
        if not hasattr(filtered, '__len__'):
            filtered = list(filtered)
        if filtered:
            return self.reduce(filtered)
        return self.get_default_value()

    @classmethod
    def calculate_for_all_apps(cls, qset=None):
        if not qset:
            from intake.models import Applicant
            from intake.serializers import ApplicantSerializer
            qset = Applicant.objects.all()
        field = cls()
        return field.to_representation(
            ApplicantSerializer(qset, many=True).data
            )


class FinishedCountField(ApplicationAggregateField):

    def get_default_value(self):
        return 0

    def filter(self, applications):
        return truthy_values_filter(applications, 'finished')


class MeanCompletionTimeField(ApplicationAggregateField):
    def filter(self, applications, org):
        """Only include applications that have both finished and started times
        """
        return single_org_filter(
            truthy_values_filter(applications, 'finished', 'started'),
            org)

    def reduce(self, applications):
        return statistics.mean(seconds_to_complete(applications))


class MedianCompletionTimeField(MeanCompletionTimeField):
    def reduce(self, applications):
        return statistics.median(seconds_to_complete(applications))


class DropOff(ApplicationAggregateField):

    def get_default_value(self):
        return 0

    def filter(self, applications):
        return truthy_values_filter(applications, 'started')

    def reduce(self, applications):
        """Return the number of finished apps as a fraction of started apps
        """
        total = len(applications)
        finished = len(list(truthy_values_filter(applications, 'finished')))
        return 1.0 - (finished / total)


class MultiCountyField(ApplicationAggregateField):

    def reduce(self, applications):
        total = len(applications)
        multicounty = len(list(
            truthy_values_filter(applications, 'is_multicounty')))
        return multicounty / total


class WeeklyTotals(ApplicationAggregateField):
    start_date = datetime.date(2016, 4, 18)

    def get_lookup_structure(self):
        today = get_todays_date()
        duration = today - self.start_date
        number_of_days = duration.days
        structure = [
                (today - datetime.timedelta(days=i), [])
                for i in range(0, number_of_days, 7)
            ]
        return structure

    def filter(self, applications):
        """
        Filter down to finished applications within the designated time span
        in buckets
        """
        day_buckets = self.get_lookup_structure()
        num_weeks = len(day_buckets)
        for app in truthy_values_filter(applications, 'finished'):
            date = app['finished'].date()
            added = False
            index = 1
            while (not added) and (index < num_weeks):
                week_end_date, weeks_apps = day_buckets[index]
                if date > week_end_date:
                    day_buckets[index - 1][1].append(app)
                    added = True
                index += 1
        return day_buckets

    def reduce(self, buckets):
        """Bucket applications by day, get counts for each day
        """
        return [
            dict(
                date=day.isoformat(),
                count=len(apps)
                )
            for day, apps in reversed(buckets)
            ]


class AppsThisWeek(ApplicationAggregateField):

    def filter(self, applications):
        today = get_todays_date()
        a_week_ago = today - datetime.timedelta(days=7)
        for app in truthy_values_filter(applications, 'finished'):
            if app['finished'].date() > a_week_ago:
                yield app

    def reduce(self, applications):
        return len(applications)


class Channels(ApplicationAggregateField):

    visitor_tally_sql = """
select referrer, count(*) as total
from intake_visitor
group by referrer
order by count(*) desc
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_visitor_tally_date = None
        self.visitor_tally = {}

    def get_default_value(self):
        return []

    def get_visitor_tally_if_needed(self):
        today = get_todays_date()
        tallied_today = self.last_visitor_tally_date == today
        if not tallied_today:
            self.get_new_visitor_tally()
        return self.visitor_tally

    def get_new_visitor_tally(self):
        with connection.cursor() as cursor:
            cursor.execute(self.visitor_tally_sql)
            rows = cursor.fetchall()
        totals = {}
        for referrer, total in rows:
            host = parse_url_host(referrer)
            if host not in totals:
                totals[host] = 0
            totals[host] += total
        self.visitor_tally = totals
        self.last_visitor_tally_date = get_todays_date()

    def filter(self, applications):
        return truthy_values_filter(
            applications, 'started', 'finished', 'visitor_id')

    def reduce(self, applications):
        total = len(applications)
        # get referrer counts for submitted apps
        referrer_counts = collections.Counter([
            parse_url_host(app['referrer']) for app in applications])
        results = []
        # pull in referrer counts for visitors
        hits_lookup = self.get_visitor_tally_if_needed()
        for referrer, app_count in referrer_counts.items():
            data = dict(
                channel=referrer,
                percent_of_apps=app_count / total,
                apps=app_count,
                )
            hits = hits_lookup.get(referrer)
            if hits:
                data['hits'] = hits
                data['conversion_rate'] = app_count / hits
            else:
                data['hits'] = 0
                data['conversion_rate'] = 1.0
            if referrer == '':
                data['channel'] = 'DIRECT'
            results.append(data)
        results.sort(key=lambda d: d['percent_of_apps'], reverse=True)
        return results


class ErrorRate(ApplicationAggregateField):

    def get_default_value(self):
        return 0

    def filter(self, applications):
        today = get_todays_date()
        a_week_ago = today - datetime.timedelta(days=7)
        for app in truthy_values_filter(applications, 'started'):
            if app['started'].date() > a_week_ago:
                yield app

    def reduce(self, applications):
        error_count = len([app for app in applications if app['had_errors']])
        total = len(applications)
        return error_count / total


class WhereTheyHeard(ApplicationAggregateField):

    def get_default_value(self):
        return []

    def filter(self, applications):
        today = get_todays_date()
        a_week_ago = today - datetime.timedelta(days=7)
        for app in truthy_values_filter(
                applications, 'where_they_heard', 'finished'):
            if app['finished'].date() > a_week_ago:
                yield app

    def reduce(self, applications):
        counts = list(collections.Counter([
            parse_self_reported_referral(app['where_they_heard'])
            for app in applications
        ]).items())
        counts.sort(key=lambda a: a[1], reverse=True)
        return counts


class ContactPreferencesCount(ApplicationAggregateField):

    def get_default_value(self):
        return []

    def filter(self, applications):
        return truthy_values_filter(applications, 'finished')

    def reduce(self, applications):
        counter = collections.Counter()
        for app in applications:
            keys = tuple(
                    key.replace('prefers_', '')
                    for key in
                    sorted(app.get('contact_preferences', []))
                )
            counter.update([keys])
        counts = list(counter.items())
        counts.sort(key=lambda a: a[1], reverse=True)
        num_apps = len(applications)
        counts = [
            (pref, count, num_apps, count / num_apps)
            for pref, count in counts
        ]
        return counts
