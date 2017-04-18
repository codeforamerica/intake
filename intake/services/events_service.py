from intake import models
import intake.services.applicants as ApplicantsService


def get_app_id(request):
    return ApplicantsService.get_applicant_from_request_or_session(request).id


def log_app_started(request, counties):
    return models.ApplicationEvent.log_app_started(
        applicant_id=get_app_id(request), counties=counties)


def log_form_page_complete(request, page_name):
    """page_name should be the class name of the view instance.
    """
    return models.ApplicationEvent.log_page_complete(
        applicant_id=get_app_id(request), page_name=page_name)


def log_form_validation_errors(request, errors):
    return models.ApplicationEvent.log_app_errors(
        applicant_id=get_app_id(request), errors=errors)
