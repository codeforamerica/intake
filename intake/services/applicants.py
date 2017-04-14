from django.db.models import Count
from intake import models


def get_applicants_with_multiple_submissions():
    return models.Applicant.objects.annotate(
        sub_count=Count('form_submissions')
    ).filter(sub_count__gt=1)


# should these be using request.context_data?
# should they do a get or create for an applicant id?
# https://docs.djangoproject.com/en/1.10/ref/request-response/#attributes-set-by-middleware


def create_new_applicant(request):
    if not request.applicant:
        applicant = models.Applicant(
            visitor_id=request.visitor.id)
        applicant.save()
        request.session['applicant_id'] = applicant.id
        request.applicant = applicant
    return request.applicant


def get_applicant_from_request_or_session(request):
    if not request.applicant:
        applicant = models.Applicant.objects.filter(
            id=request.session.get('applicant_id')).first()
        if not applicant:
            return create_new_applicant(request)
        request.applicant = applicant
    return request.applicant
