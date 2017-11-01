import csv
from django.utils import timezone
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from intake.serializers.application_serializers import \
    ApplicationCSVDownloadSerializer
from intake.services.applications_service import \
    get_all_applications_for_users_org


@login_required
def csv_download(request):
    """ Creates a CSV file using all of the applications to the users
    organization.
    """
    apps = get_all_applications_for_users_org(request.user)
    data = ApplicationCSVDownloadSerializer(apps, many=True).data
    fields = []
    for datum in data:
        these_fields = list(datum.keys())
        # Finds the largest set of fields and uses it
        # There should not be a case where a smaller set of fields would have
        # a field not in a larger one.
        if len(these_fields) > len(fields):
            fields = these_fields
    response = HttpResponse(content_type='text/csv')
    csv_writer = csv.DictWriter(response, fieldnames=fields)
    csv_writer.writeheader()
    csv_writer.writerows(data)
    file = 'all_applications_to_%s_%s.csv' % (
        request.user.profile.organization.slug,
        timezone.now().strftime('%m-%d-%Y'),
    )
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    return response
