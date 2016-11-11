import datetime
import csv
import collections
import itertools
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.db.models import Min
from django.utils import timezone
from pytz import timezone as tz
from django.utils.html import mark_safe
from rest_framework.renderers import JSONRenderer

from intake import models, serializers, constants, aggregate_serializers
from intake.aggregate_serializer_fields import truthy_values_filter

PACIFIC = tz('US/Pacific')

ALL = 'all'


def get_serialized_applications():
    apps = models.Applicant.objects.prefetch_related(
            'form_submissions',
            'form_submissions__organizations',
            'events')
    return serializers.ApplicantSerializer(apps, many=True).data


def get_day_data_dict(week_of_apps_grouped_by_day):
    if not week_of_apps_grouped_by_day:
        week_of_apps_grouped_by_day = [[]]
    return dict(
        applications_today=week_of_apps_grouped_by_day[-1],
        applications_this_week=list(
            itertools.chain(*week_of_apps_grouped_by_day)
            )
    )


def app_date(app):
    dt = app['finished'] if app['finished'] else app['started']
    if dt is None:
        import ipdb; ipdb.set_trace()
    return dt.date()


def app_org_slugs(app):
    return [org['slug'] for org in app.get('organizations', [])]


def is_valid_app(app):
    for key in ('started', 'finished'):
        if app.get(key):
            return True
    return False


def breakup_apps_by_org(apps):
    org_buckets = {
        ALL: {
            'org': {
                'slug': ALL,
                'name': 'All Organizations'
            },
            'apps': []
        }
    }
    for app in apps:
        if is_valid_app(app):
            org_buckets[ALL]['apps'].append(app)
            for org in app.get('organizations', []):
                slug = org['slug']
                if slug not in org_buckets:
                    org_buckets[slug] = {
                        'org': org,
                        'apps': []
                    }
                org_buckets[slug]['apps'].append(app)
    return org_buckets


def get_todays_date():
    return timezone.now().astimezone(PACIFIC).date()


def get_day_lookup_structure():
    number_of_days = 62
    two_months = datetime.timedelta(days=number_of_days)
    today = get_todays_date()
    two_months_ago = today - two_months
    return collections.OrderedDict(
        [
            (two_months_ago + datetime.timedelta(days=i), [])
            for i in range(number_of_days)
        ])


def get_application_day_buckets(apps, ):
    day_lookup = get_day_lookup_structure()
    for app in apps:
        day = app_date(app)
        if day in day_lookup:
            day_lookup[day].append(app)
    app_sets = list(day_lookup.values())
    day_buckets = []
    for i in range(len(app_sets)):
        if i < 7:
            week_for_day = app_sets[:i]
        else:
            week_for_day = app_sets[i-7:i]
        day_buckets.append(get_day_data_dict(week_for_day))
    return day_buckets


def get_serialized_day_data(apps, serializer):
    buckets = get_application_day_buckets(apps)
    return serializer(buckets, many=True).data


def get_aggregate_day_data(apps, private=False):
    serializer = aggregate_serializers.PublicDaySerializer
    if private:
        serializer = aggregate_serializers.PrivateDaySerializer
    day_dicts = get_serialized_day_data(apps, serializer)
    total_count = len(list(truthy_values_filter(apps, 'finished')))
    return {
        'days': list(day_dicts),
        'total': total_count
    }


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        show_private_data = self.request.user.is_staff
        context = super().get_context_data(**kwargs)
        all_apps = get_serialized_applications()
        apps_by_org = list(breakup_apps_by_org(all_apps).values())
        for group in apps_by_org:
            org_apps = group.pop('apps', [])
            group.update(get_aggregate_day_data(org_apps, show_private_data))
        context['stats'] = {
            'org_stats': apps_by_org,
        }
        return context


class DailyTotals(View):
    """A Downloadable CSV with daily totals for each county
    """

    def get(self, request):
        totals = list(models.FormSubmission.get_daily_totals())
        response = HttpResponse(content_type='text/csv')
        filename = 'daily_totals.csv'
        content_disposition = 'attachment; filename="{}"'.format(filename)
        response['Content-Disposition'] = content_disposition
        keys = [
            "Day", "All",
            constants.CountyNames.SAN_FRANCISCO,
            constants.CountyNames.CONTRA_COSTA,
            constants.CountyNames.ALAMEDA,
        ]
        writer = csv.DictWriter(
            response,
            fieldnames=keys,
            quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for item in totals:
            writer.writerow(item)
        return response


stats = Stats.as_view()
daily_totals = DailyTotals.as_view()
