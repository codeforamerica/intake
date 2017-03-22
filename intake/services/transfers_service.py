from django.utils.translation import ugettext_lazy as _
from intake import models, notifications


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
    intro, body = render_application_transfer_message(**transfer_data)
    notifications.send_simple_front_notification(
        contact_info, "\n\n".join([intro, body]))


def transfer_application(author, application, to_organization, reason):
    """Transfers an application from one organization to another
    """
    transfer_status_update = models.StatusUpdate(
        status_type_id=models.status_type.TRANSFERRED,
        author_id=author.id,
        application=application
    )
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
    return transfer


def transfer_application_and_notify_applicant(transfer_data):
    transfer_application(
        author=transfer_data['author'],
        application=transfer_data['application'],
        to_organization=transfer_data['to_organization'],
        reason=transfer_data.get('reason', ''))
    send_application_transfer_notification(transfer_data)
