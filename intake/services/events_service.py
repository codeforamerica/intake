from intake import models
import intake.services.applicants as ApplicantsService
import project.services.logging_service as LoggingService
from project.services.mixpanel_service import log_to_mixpanel

"""
Tab separated? Space separated?
key=valuekey2="value2"
page_name="/url/"
https://docs.djangoproject.com/en/1.11/topics/logging/#making-logging-calls

Goals:
- everything that goes to mixpanel is logged to stdout
- we can add lots of properties on the fly easily to both mixpanel & std out
- easy to add new calls in the codebase

"""


def get_app_id(request):
    return ApplicantsService.get_applicant_from_request_or_session(request).id


def app_started(request, counties):
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        request)
    return models.ApplicationEvent.log_app_started(
        applicant_id=applicant.id,
        counties=counties,
        referrer=applicant.visitor.referrer,
        source=applicant.visitor.source,
        user_agent=request.META.get('HTTP_USER_AGENT'))


def form_page_complete(request, page_name):
    """page_name should be the class name of the view instance.
    """
    return models.ApplicationEvent.log_page_complete(
        applicant_id=get_app_id(request), page_name=page_name)


def form_validation_errors(request, errors):
    return models.ApplicationEvent.log_app_errors(
        applicant_id=get_app_id(request), errors=errors)


def page_viewed(visitor, page_name):
    name = 'page_viewed'
    LoggingService.format_and_log(
        visitor_uuid=visitor.get_uuid(), action=name, page_name=page_name)
    log_to_mixpanel(
        visitor.get_uuid(), event_name=name, page_name=page_name)


def status_update_sent(status_update):
    event_kwargs = dict(
        distinct_id=status_update.application.form_submission.get_uuid(),
        event_name='app_status_updated',
        user_email=status_update.author.email,
        application_id=status_update.application.id,
        status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()],
        has_additional_info=bool(status_update.additional_information),
        organization_name=status_update.author.profile.organization.name)
    if hasattr(status_update, 'notification'):
        event_kwargs.update(
            notification_contact_info_types=list(
                status_update.notification.contact_info.keys()))
    log_to_mixpanel(**event_kwargs)


def app_index_viewed(user, applications):
    name = 'app_index_viewed'
    LoggingService.format_and_log(
        user_id=user.id, action=name, applications_displayed=[
            app.id for app in applications])


def event(name, tracking_id):
    """
    this is likely where we would log events that go to std_out / the
    debugger log, but which do not go to mixpanel and which do not fit
    neatly into the other defined event groups
    """
    pass


def application_event():
    """
    this is for events that happen once an application has been created,
    i.e. status updates
    """
    pass


def applicant_event():
    """
    this is for events that relate to an applicant, generally includes those
    relating to the process of completing a formsubmission or reciving a
    followup
    """
    pass


def visitor_event():
    """
    this is for events that relate to visitors who have not yet started an
    application, i.e. page views
    """
    pass


def user_event():
    """
    this is for events relating to CFA or org users, such as opening an app,
    and may form the base for the audit log eventually
    """
    pass
