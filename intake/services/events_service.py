import logging
from django.utils import timezone
from intake import models
import intake.services.applicants as ApplicantsService
from intake.tasks import log_to_mixpanel

"""
key=value key2="value2"
page_name="/url/"
https://docs.djangoproject.com/en/1.11/topics/logging/#making-logging-calls
"""

logger = logging.getLogger(__name__)

timestamp_format = '%Y-%m-%d %H:%M:%S.%f'

def format_and_log(**data):
    # format as string

    # get now and format
    # pass to logger


def get_app_id(request):
    return ApplicantsService.get_applicant_from_request_or_session(request).id


def log_app_started(request, counties):
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        request)
    return models.ApplicationEvent.log_app_started(
        applicant_id=applicant.id,
        counties=counties,
        referrer=applicant.visitor.referrer,
        source=applicant.visitor.source,
        user_agent=request.META.get('HTTP_USER_AGENT'))


def log_form_page_complete(request, page_name):
    """page_name should be the class name of the view instance.
    """
    return models.ApplicationEvent.log_page_complete(
        applicant_id=get_app_id(request), page_name=page_name)


def log_form_validation_errors(request, errors):
    return models.ApplicationEvent.log_app_errors(
        applicant_id=get_app_id(request), errors=errors)


def log_page_viewed(visitor, page_name):
    name = 'page_viewed'
    format_and_log(
        visitor_uuid=visitor.get_uuid(), action=name, page_name=page_name)
    log_to_mixpanel(
        visitor.get_uuid(), event_name=name, page_name=page_name)


def log_status_updated(application, status_update):
    name = 'status_updated'
    format_and_log(
        applicant_uuid=application.form_submisssion.applicant.get_uuid(),
        user_id=status_update.author.id,
        action=name, status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()])
    log_to_mixpanel(
        applicant_uuid=application.form_submisssion.applicant.get_uuid(),
        event_name=name, user_uuid=status_update.author.get_uuid(),
        action=name, status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()])


def log_app_index_viewed(user, applications):
    name = 'app_index_viewed'
    format_and_log(
        user_id=user.id, action=name, applications_displayed=[
            app.id for app in applications])


def log_event(name, tracking_id):
    pass


def log_application_event():
    pass


def log_applicant_event():
    pass


def log_visitor_event():
    pass


def log_user_event():
    pass
