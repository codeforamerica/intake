from django.db.models import Count
from intake import models


def get_applicants_with_multiple_submissions():
    return models.Applicant.objects.annotate(
        sub_count=Count('form_submissions')
    ).filter(sub_count__gt=1)


def create_new_applicant(request):
    if not getattr(request, 'applicant', None):
        applicant, created = models.Applicant.objects.get_or_create(
            visitor_id=request.visitor.id)
        request.session['applicant_id'] = applicant.id
        request.applicant = applicant
    return request.applicant


def get_applicant_from_request_or_session(request):
    if not getattr(request, 'applicant', None):
        applicant = models.Applicant.objects.filter(
            id=request.session.get('applicant_id')).first()
        request.applicant = applicant
    return request.applicant
