
from django.db.models import Count
from intake import models


def get_applicants_with_multiple_submissions():
    return models.Applicant.objects.annotate(
        sub_count=Count('form_submissions')
    ).filter(sub_count__gt=1)
