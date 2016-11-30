import csv
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView

from intake import models, serializers, constants, aggregate_serializers


def is_valid_app(app):
    for key in ('started', 'finished'):
        if app.get(key):
            return True
    return False


def get_serialized_applications():
    apps = models.Applicant.objects.prefetch_related(
            'form_submissions',
            'form_submissions__organizations',
            'events')
    return serializers.ApplicantSerializer(apps, many=True).data


def breakup_apps_by_org(apps):
    org_buckets = {
        constants.Organizations.ALL: {
            'org': {
                'slug': constants.Organizations.ALL,
                'name': 'Total (All Organizations)'
            },
            'apps': []
        }
    }
    for app in apps:
        if is_valid_app(app):
            org_buckets[constants.Organizations.ALL]['apps'].append(app)
            for org in app.get('organizations', []):
                slug = org['slug']
                if slug not in org_buckets:
                    org_buckets[slug] = {
                        'org': org,
                        'apps': []
                    }
                org_buckets[slug]['apps'].append(app)
    return list(org_buckets.values())


def organization_index(serialized_org):
    return constants.DEFAULT_ORGANIZATION_ORDER.index(
        serialized_org['org']['slug'])


def add_stats_for_org(org_data, Serializer):
    org_apps = org_data.pop('apps', [])
    input_data = {'apps': org_apps}
    results = Serializer(input_data).data
    org_data.update(results)


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        show_private_data = self.request.user.is_staff
        context = super().get_context_data(**kwargs)
        all_apps = get_serialized_applications()
        apps_by_org = breakup_apps_by_org(all_apps)
        apps_by_org.sort(key=organization_index)
        Serializer = aggregate_serializers.PublicStatsSerializer
        if show_private_data:
            Serializer = aggregate_serializers.PrivateStatsSerializer
        for org_data in apps_by_org:
            add_stats_for_org(org_data, Serializer)
        context['stats'] = {'org_stats': apps_by_org}
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
            constants.CountyNames.MONTEREY,
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
