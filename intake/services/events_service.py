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


# ### NEW EVENTS ###


def page_viewed(visitor, url):
    event_name = 'page_viewed'
    log_to_mixpanel(
        distinct_id=visitor.get_uuid(),
        event_name=event_name,
        url=url,
        referrer=visitor.referrer,
        source=visitor.source)


def site_entered(visitor, url):
    event_name = 'site_entered'
    log_to_mixpanel(
        distinct_id=visitor.get_uuid(),
        event_name=event_name,
        url=url,
        referrer=visitor.referrer,
        source=visitor.source)


def app_transferred(old_application, new_application, user):
    event_name = 'app_transferred'
    log_to_mixpanel(
        distinct_id=old_application.form_submission.get_uuid(),
        event_name=event_name,
        user_email=user.email,
        from_application_id=old_application.id,
        to_application_id=new_application.id,
        from_organization_name=old_application.organization.name,
        to_organization_name=new_application.organization.name)


def tags_added(tag_links):
    event_name = 'app_tag_added'
    for tag_link in tag_links:
        log_to_mixpanel(
            distinct_id=tag_link.content_object.get_uuid(),
            event_name=event_name,
            tag_name=tag_link.tag.name,
            author_email=tag_link.user.email)


def note_added(submission, user):
    event_name = 'app_note_added'
    log_to_mixpanel(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        author_email=user.email)


def followup_sent(submission, contact_methods):
    event_name = 'app_followup_sent'
    log_to_mixpanel(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        contact_info_types=contact_methods)


def app_opened(application, user):
    event_name = 'app_opened'
    log_to_mixpanel(
        distinct_id=application.form_submission.get_uuid(),
        event_name=event_name,
        application_id=application.id,
        application_organization_name=application.organization.name,
        user_email=user.email,
        user_organization_name=user.profile.organization.name)


def bundle_opened(bundle, user):
    event_name = 'app_bundle_opened'
    for submission in bundle.submissions.all():
        application = submission.applications.filter(
                organization_id=bundle.organization_id).first()
        log_to_mixpanel(
            distinct_id=submission.get_uuid(),
            event_name=event_name,
            application_id=application.id,
            bundle_id=bundle.id,
            bundle_organization_name=bundle.organization.name,
            user_email=user.email,
            user_organization_name=user.profile.organization.name)


def status_update_sent(status_update):
    event_name = 'app_status_updated'
    event_kwargs = dict(
        event_name=event_name,
        distinct_id=status_update.application.form_submission.get_uuid(),
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
