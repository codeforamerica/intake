import intake.services.applicants as ApplicantsService
import project.services.logging_service as LoggingService
from intake.services import status_notifications as SNService
from intake.tasks import log_to_mixpanel


def form_started(request, counties):
    event_name = 'application_started'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        request)
    log_to_mixpanel.delay(
        distinct_id=applicant.get_uuid(),
        event_name=event_name,
        counties=counties,
        referrer=applicant.visitor.referrer,
        source=applicant.visitor.source,
        user_agent=request.META.get('HTTP_USER_AGENT'))


def form_page_complete(request, page_name):
    """page_name should be the class name of the view instance.
    """
    event_name = 'application_page_complete'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        request)
    log_to_mixpanel.delay(
        distinct_id=applicant.get_uuid(),
        event_name=event_name,
        url=request.path,
        page_name=page_name)


def form_validation_failed(view, request, errors):
    """
    security concerns addressed here:
    MP gets just keys (avoid PII)
    std_out gets k-v pair for errors, but misses application identifiers
    """
    event_name = 'application_errors'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        request)
    for error_key, errors in errors.items():
        log_to_mixpanel.delay(
            distinct_id=applicant.get_uuid(),
            event_name=event_name,
            url=request.path,
            view_name=view.__class__.__name__,
            error=error_key)
        LoggingService.format_and_log(
            event_name, url=request.path, view_name=view.__class__.__name__,
            field=error_key, errors=errors)


def form_submitted(submission):
    event_name = 'application_submitted'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        organizations=list(
            submission.organizations.values_list('name', flat=True))
        )


def page_viewed(visitor, url):
    event_name = 'page_viewed'
    log_to_mixpanel.delay(
        distinct_id=visitor.get_uuid(),
        event_name=event_name,
        url=url,
        referrer=visitor.referrer,
        source=visitor.source)


def site_entered(visitor, url):
    event_name = 'site_entered'
    log_to_mixpanel.delay(
        distinct_id=visitor.get_uuid(),
        event_name=event_name,
        url=url,
        referrer=visitor.referrer,
        source=visitor.source)


def app_transferred(old_application, new_application, user):
    event_name = 'app_transferred'
    log_to_mixpanel.delay(
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
        log_to_mixpanel.delay(
            distinct_id=tag_link.content_object.get_uuid(),
            event_name=event_name,
            tag_name=tag_link.tag.name,
            author_email=tag_link.user.email)


def note_added(submission, user):
    event_name = 'app_note_added'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        author_email=user.email)


def followup_sent(submission, contact_methods):
    event_name = 'app_followup_sent'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        contact_info_types=contact_methods)


def confirmation_sent(submission, contact_methods):
    event_name = 'app_confirmation_sent'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        contact_info_types=contact_methods)


def apps_opened(applications, user):
    event_name = 'app_opened'
    for application in applications:
        log_to_mixpanel.delay(
            distinct_id=application.form_submission.get_uuid(),
            event_name=event_name,
            application_id=application.id,
            application_organization_name=application.organization.name,
            user_email=user.email,
            user_organization_name=user.profile.organization.name)


def bundle_opened(bundle, user):
    event_name = 'app_bundle_opened'
    for submission in bundle.submissions.all():
        log_to_mixpanel.delay(
            distinct_id=submission.get_uuid(),
            event_name=event_name,
            bundle_id=bundle.id,
            bundle_organization_name=bundle.organization.name,
            user_email=user.email,
            user_organization_name=user.profile.organization.name)


def status_updated(status_update):
    event_name = 'app_status_updated'
    event_kwargs = dict(
        distinct_id=status_update.application.form_submission.get_uuid(),
        event_name=event_name,
        user_email=status_update.author.email,
        application_id=status_update.application.id,
        status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()],
        additional_info_length=len(status_update.additional_information),
        other_next_steps_length=len(status_update.other_next_step),
        organization_name=status_update.author.profile.organization.name,
        message_change_ratio=SNService.get_message_change_ratio(status_update),
        contact_info_keys=SNService.get_contact_info_keys(status_update),
        has_unsent_additional_info=SNService.has_unsent_additional_info(
            status_update),
        has_unsent_other_next_step=SNService.has_unsent_other_next_step(
            status_update),
        )
    if hasattr(status_update, 'notification'):
        event_kwargs.update(
            notification_contact_info_types=list(
                status_update.notification.contact_info.keys()))
    log_to_mixpanel.delay(**event_kwargs)


def partnership_interest_submitted(partnership_lead):
    event_name = 'partnership_interest_submitted'
    log_to_mixpanel.delay(
        distinct_id=partnership_lead.visitor.get_uuid(),
        event_name=event_name)
