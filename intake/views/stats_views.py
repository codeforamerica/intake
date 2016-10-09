import datetime
import csv
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.db.models import Min
from django.utils import timezone
from django.utils.html import mark_safe
from rest_framework.renderers import JSONRenderer

from intake import models, serializers, constants


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        county_totals = []
        counties = models.County.objects.all()
        for county in counties:
            county_totals.append(dict(
                count=models.FormSubmission.objects.filter(
                    organizations__county=county).count(),
                county_name=county.name))
        context['stats'] = {
            'total_all_counties': models.FormSubmission.objects.count(),
            'county_totals': county_totals
        }
        if self.request.user.is_authenticated():
            two_months = datetime.timedelta(days=62)
            two_months_ago = timezone.now() - two_months
            applicants = models.Applicant.objects\
                .annotate(first_event=Min('events__time'))\
                .filter(first_event__gte=two_months_ago)\
                .order_by('-first_event')
            if not self.request.user.is_staff:
                org = self.request.user.profile.organization
                applicants = applicants.filter(
                    form_submissions__organizations=org)
            json = JSONRenderer().render(
                serializers.ApplicantSerializer(applicants, many=True).data)
            context['applications_json'] = mark_safe(json.decode('utf-8'))
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
