import intake.services.applicants as ApplicantsService
import project.services.logging_service as LoggingService
from intake.services import status_notifications as SNService
from intake.tasks import log_to_mixpanel
from intake.serializers import (
    mixpanel_request_data, mixpanel_applicant_data, mixpanel_view_data)
from user_accounts.serializers import mixpanel_user_data


def mixpanel_data_from_view_request_user(view, request=None, user=None):
    """Extracts basic data from a view, request, and user for mixpanel.
    If request and user are not explicitly passed, this function will
    attempt to extract both from the view.
    """
    data = mixpanel_view_data(view)
    request = request or getattr(view, 'request', None)
    user = user or getattr(request, 'user', None)
    if request:
        data.update(mixpanel_request_data(view.request))
    if user and getattr(user, 'is_authenticated', False):
        data.update(mixpanel_user_data(user))
    return data


def form_started(view, counties):
    event_name = 'application_started'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        view.request)
    log_to_mixpanel.delay(
        distinct_id=applicant.get_uuid(),
        event_name=event_name,
        counties=counties,
        **mixpanel_applicant_data(applicant),
        **mixpanel_data_from_view_request_user(view))


def form_page_complete(view):
    """page_name should be the class name of the view instance.
    """
    event_name = 'application_page_complete'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        view.request)
    log_to_mixpanel.delay(
        distinct_id=applicant.get_uuid(),
        event_name=event_name,
        **mixpanel_applicant_data(applicant),
        **mixpanel_data_from_view_request_user(view))


def form_validation_failed(view, errors):
    """
    security concerns addressed here:
    MP gets just keys (avoid PII)
    std_out gets k-v pair for errors, but misses application identifiers
    """
    event_name = 'application_errors'
    applicant = ApplicantsService.get_applicant_from_request_or_session(
        view.request)
    for error_key, errors in errors.items():
        log_to_mixpanel.delay(
            distinct_id=applicant.get_uuid(),
            event_name=event_name,
            error=error_key,
            **mixpanel_applicant_data(applicant),
            **mixpanel_data_from_view_request_user(view))
        LoggingService.format_and_log(
            event_name, url=view.request.path,
            view_name=view.__class__.__name__, field=error_key, errors=errors)


def form_submitted(view, submission):
    event_name = 'application_submitted'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        organizations=list(
            submission.organizations.values_list('name', flat=True)),
        **mixpanel_applicant_data(submission.applicant),
        **mixpanel_data_from_view_request_user(view))


def site_entered(visitor, request):
    event_name = 'site_entered'
    log_to_mixpanel.delay(
        distinct_id=visitor.get_uuid(),
        event_name=event_name,
        **mixpanel_request_data(request))


def page_viewed(request, response):
    event_name = 'page_viewed'
    data = dict(
        distinct_id=request.visitor.get_uuid(),
        event_name=event_name,
        **mixpanel_request_data(request))
    if response.view:
        data.update(mixpanel_view_data(response.view))
    log_to_mixpanel.delay(**data)


def app_transferred(old_application, new_application, user):
    event_name = 'app_transferred'
    log_to_mixpanel.delay(
        distinct_id=old_application.form_submission.get_uuid(),
        event_name=event_name,
        user_email=user.email,
        from_application_id=old_application.id,
        to_application_id=new_application.id,
        from_organization_name=old_application.organization.name,
        to_organization_name=new_application.organization.name,
        **mixpanel_applicant_data(old_application.form_submission.applicant),
        **mixpanel_user_data(user))


def tags_added(tag_links):
    event_name = 'app_tag_added'
    for tag_link in tag_links:
        log_to_mixpanel.delay(
            distinct_id=tag_link.content_object.get_uuid(),
            event_name=event_name,
            tag_name=tag_link.tag.name,
            **mixpanel_applicant_data(tag_link.content_object.applicant),
            **mixpanel_user_data(tag_link.user))


def note_added(view, submission):
    event_name = 'app_note_added'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        **mixpanel_applicant_data(submission.applicant),
        **mixpanel_data_from_view_request_user(view))


def followup_sent(submission, contact_methods):
    event_name = 'app_followup_sent'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        contact_info_types=contact_methods,
        **mixpanel_applicant_data(submission.applicant))


def confirmation_sent(submission, contact_methods):
    event_name = 'app_confirmation_sent'
    log_to_mixpanel.delay(
        distinct_id=submission.get_uuid(),
        event_name=event_name,
        contact_info_types=contact_methods,
        **mixpanel_applicant_data(submission.applicant))


def apps_opened(view, applications):
    event_name = 'app_opened'
    for application in applications:
        log_to_mixpanel.delay(
            distinct_id=application.form_submission.get_uuid(),
            event_name=event_name,
            application_id=application.id,
            application_organization_name=application.organization.name,
            **mixpanel_applicant_data(application.form_submission.applicant),
            **mixpanel_data_from_view_request_user(view))


def bundle_opened(bundle, user):
    """Deprecated. Do not use.
    """
    event_name = 'app_bundle_opened'
    for submission in bundle.submissions.all():
        log_to_mixpanel.delay(
            distinct_id=submission.get_uuid(),
            event_name=event_name,
            bundle_id=bundle.id,
            bundle_organization_name=bundle.organization.name,
            user_email=user.email,
            user_organization_name=user.profile.organization.name)


def status_updated(view, status_update):
    event_name = 'app_status_updated'
    event_kwargs = dict(
        distinct_id=status_update.application.form_submission.get_uuid(),
        event_name=event_name,
        application_id=status_update.application.id,
        status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()],
        additional_info_length=len(status_update.additional_information),
        other_next_steps_length=len(status_update.other_next_step),
        message_change_ratio=SNService.get_message_change_ratio(status_update),
        contact_info_keys=SNService.get_contact_info_keys(status_update),
        has_unsent_additional_info=SNService.has_unsent_additional_info(
            status_update),
        has_unsent_other_next_step=SNService.has_unsent_other_next_step(
            status_update),
        **mixpanel_applicant_data(
            status_update.application.form_submission.applicant),
        **mixpanel_data_from_view_request_user(view))
    if hasattr(status_update, 'notification'):
        event_kwargs.update(
            notification_contact_info_types=list(
                status_update.notification.contact_info.keys()))
    log_to_mixpanel.delay(**event_kwargs)


def partnership_interest_submitted(view, partnership_lead):
    event_name = 'partnership_interest_submitted'
    log_to_mixpanel.delay(
        distinct_id=partnership_lead.visitor.get_uuid(),
        event_name=event_name,
        **mixpanel_data_from_view_request_user(view))


def empty_print_all_opened(request, view):
    # not currently used
    event_name = 'user_empty_print_all_opened'
    log_to_mixpanel.delay(
        distinct_id=request.user.get_uuid(),
        event_name=event_name)


def unread_pdf_opened(request, view):
    # not currently used
    applicant_event_name = 'app_unread_pdf_opened'
    user_event_name = 'user_unread_pdf_opened'
    log_to_mixpanel.delay(
        distinct_id=request.user.get_uuid(),
        event_name=user_event_name,
        organization_name=view.organization.name)
    for app in view.applications:
        log_to_mixpanel.delay(
            distinct_id=app.get_uuid(),
            event_name=applicant_event_name,
            bundle_organization_name=app.organization.name,
            user_email=request.user.email,
            user_organization_name=request.user.profile.organization.name)


def user_page_viewed(request, response):
    event_name = 'user_page_viewed'
    data = dict(
        distinct_id=request.visitor.get_uuid(),
        event_name=event_name,
        **mixpanel_request_data(request),
        **mixpanel_user_data(request.user))
    if response.view:
        data.update(mixpanel_view_data(response.view))
    log_to_mixpanel.delay(**data)


def user_login(view):
    event_name = 'user_login'
    log_to_mixpanel.delay(
        distinct_id=view.request.user.profile.get_uuid(),
        event_name=event_name,
        **mixpanel_data_from_view_request_user(view))


def user_account_created(view):
    # this doesn't appear to be used
    event_name = 'user_account_created'
    log_to_mixpanel.delay(
        distinct_id=view.user.profile.get_uuid(),
        event_name=event_name,
        **mixpanel_data_from_view_request_user(view))


def user_failed_login(view):
    event_name = 'user_failed_login'
    log_to_mixpanel.delay(
        distinct_id=view.request.visitor.get_uuid(),
        event_name=event_name,
        attempted_login=view.request.POST.get('login', ''),
        **mixpanel_data_from_view_request_user(view))


def user_reset_password(view, email):
    event_name = 'user_reset_password'
    log_to_mixpanel.delay(
        distinct_id=view.request.visitor.get_uuid(),
        event_name=event_name,
        email=email,
        **mixpanel_data_from_view_request_user(view))


def user_email_link_clicked(view):
    event_name = 'user_email_link_clicked'
    log_to_mixpanel.delay(
        distinct_id=view.request.user.profile.get_uuid(),
        event_name=event_name,
        target_url=view.get_redirect_url(),
        **mixpanel_data_from_view_request_user(view))


def user_status_updated(view, status_update):
    event_name = 'user_status_updated'
    event_kwargs = dict(
        distinct_id=status_update.author.profile.get_uuid(),
        event_name=event_name,
        applicant_uuid=status_update.application.form_submission.get_uuid(),
        application_id=status_update.application.id,
        status_type=status_update.status_type.display_name,
        next_steps=[
            step.display_name for step in status_update.next_steps.all()],
        additional_info_length=len(status_update.additional_information),
        other_next_steps_length=len(status_update.other_next_step),
        message_change_ratio=SNService.get_message_change_ratio(status_update),
        contact_info_keys=SNService.get_contact_info_keys(status_update),
        has_unsent_additional_info=SNService.has_unsent_additional_info(
            status_update),
        has_unsent_other_next_step=SNService.has_unsent_other_next_step(
            status_update),
        **mixpanel_applicant_data(
            status_update.application.form_submission.applicant),
        **mixpanel_data_from_view_request_user(view))
    if hasattr(status_update, 'notification'):
        event_kwargs.update(
            notification_contact_info_types=list(
                status_update.notification.contact_info.keys()))
    log_to_mixpanel.delay(**event_kwargs)


def user_apps_opened(view, applications):
    event_name = 'user_app_opened'
    for application in applications:
        log_to_mixpanel.delay(
            distinct_id=view.request.user.profile.get_uuid(),
            event_name=event_name,
            application_id=application.id,
            applicant_uuid=application.form_submission.get_uuid(),
            application_organization_name=application.organization.name,
            **mixpanel_applicant_data(application.form_submission.applicant),
            **mixpanel_data_from_view_request_user(view)
            )


def user_app_transferred(old_application, new_application, user):
    event_name = 'user_app_transferred'
    log_to_mixpanel.delay(
        distinct_id=user.profile.get_uuid(),
        event_name=event_name,
        applicant_uuid=old_application.form_submission.get_uuid(),
        from_org=old_application.organization.name,
        to_org=new_application.organization.name,
        **mixpanel_applicant_data(old_application.form_submission.applicant),
        **mixpanel_user_data(user))


def user_apps_searched(view):
    event_name = 'user_apps_searched'
    log_to_mixpanel.delay(
        distinct_id=view.request.user.profile.get_uuid(),
        event_name=event_name,
        **mixpanel_data_from_view_request_user(view))
