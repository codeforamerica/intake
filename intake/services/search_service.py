from django.db.models import Q
from intake import models


def filter_submissions_with_querystring(submissions_queryset, query_string):
    """Filters a FormSubmission queryset based on a query_string
    """
    return submissions_queryset.filter(
            Q(first_name__icontains=query_string) |
            Q(last_name__icontains=query_string) |
            Q(ssn__icontains=query_string) |
            Q(last_four__icontains=query_string) |
            Q(drivers_license_or_id__icontains=query_string) |
            Q(phone_number__icontains=query_string) |
            Q(alternate_phone_number__icontains=query_string) |
            Q(email__icontains=query_string) |
            Q(case_number__icontains=query_string)
    )


def get_submissions_with_querystring(query_string):
    """Filters through all FormSubmissions based on the query_string
    """
    return filter_submissions_with_querystring(
        models.FormSubmission.objects.all(), query_string)


def get_applications_with_query_string(query_string):
    """Returns an Application queryset filtered down to those
        which have a form_submission matching the query_string
    """
    matching_subs = get_submissions_with_querystring(query_string)
    return models.Application.objects.filter(
        form_submission_id__in=matching_subs.values_list('id', flat=True))
