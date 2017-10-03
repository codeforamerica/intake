from django.utils.translation import ugettext_lazy as _
from intake import models, notifications
import intake.services.events_service as EventsService


TRANSFER_MESSAGE_INTRO = _(
    "Clear My Record Update from {author_name} at {from_organization}:")

APPLICATION_TRANSFER_MESSAGE = _(
    "Your {county_name} County application is now being handled by "
    "{to_organization}. {next_step}")


def render_application_transfer_message(
        form_submission, author, to_organization, from_organization,
        **kwargs):
    intro = TRANSFER_MESSAGE_INTRO.format(
        author_name=author.profile.name,
        from_organization=from_organization.name)
    body = APPLICATION_TRANSFER_MESSAGE.format(
        county_name=to_organization.county.name,
        to_organization=to_organization.name,
        next_step=to_organization.short_confirmation_message)
    return intro, body


def send_application_transfer_notification(transfer_data):
    contact_info = transfer_data['form_submission'].get_usable_contact_info()
    if contact_info:
        intro, body = render_application_transfer_message(**transfer_data)
        base_message = "\n\n".join([intro, body])
        sent_message = "\n\n".join(
            [intro, transfer_data.get('sent_message', body)])
        notifications.send_simple_front_notification(
            contact_info, sent_message, subject="Update from Clear My Record")
        return models.StatusNotification(
            contact_info=contact_info,
            base_message=base_message,
            sent_message=sent_message)
    return None


def transfer_application(author, application, to_organization, reason):
    """Transfers an application from one organization to another.
    Returns three things as a tuple:
        - a new ApplicationTransfer instance
        - a new StatusUpdate instance
        - a new Application instance for the to_organization
    """
    transferred_status_type = models.StatusType.objects.get(slug='transferred')
    transfer_status_update = models.StatusUpdate(
        status_type=transferred_status_type,
        author_id=author.id,
        application=application)
    transfer_status_update.save()
    new_application = models.Application(
        form_submission_id=application.form_submission_id,
        organization=to_organization)
    new_application.save()
    transfer = models.ApplicationTransfer(
        status_update=transfer_status_update,
        new_application=new_application,
        reason=reason)
    transfer.save()
    application.was_transferred_out = True
    application.save()
    EventsService.app_transferred(application, new_application, author)
    EventsService.user_app_transferred(application, new_application, author)
    return transfer, transfer_status_update, new_application


def transfer_application_and_notify_applicant(transfer_data):
    transfer, status_update, new_app = transfer_application(
        author=transfer_data['author'],
        application=transfer_data['application'],
        to_organization=transfer_data['to_organization'],
        reason=transfer_data.get('reason', ''))
    notification = \
        send_application_transfer_notification(transfer_data)
    if notification:
        notification.status_update_id = status_update.id
        notification.save()
