from django.contrib import messages
from intake import models, notifications
import intake.services.submissions as SubmissionsService


def get_base_message_from_status_update_data(status_update_data):
    # TODO: render templates with correct data and template context
    base_template = \
        "{intro}\n{status_type_message}{additional_info}{next_step_messages}"
    intro = "Clear My Record update from {} at {}:".format(
        status_update_data['author'].profile.name,
        status_update_data['author'].profile.organization.name)
    return base_template.format(
        intro=intro,
        status_type_message=status_update_data['status_type'].template,
        additional_info=status_update_data['additional_information'],
        next_step_messages=' '.join([
            next_step.template
            for next_step in status_update_data.get('next_steps', [])
            ]))


def send_and_save_new_status(request, notification_data, status_update_data):
    next_steps = status_update_data.pop('next_steps', [])
    status_update = models.StatusUpdate(**status_update_data)
    status_update.save()
    status_update.next_steps.add(*next_steps)
    sub = status_update_data['application'].form_submission
    contact_info = SubmissionsService.get_usable_contact_info(sub)
    notification_data.update(
        base_message=get_base_message_from_status_update_data(
            status_update_data),
        status_update=status_update,
        contact_info=contact_info)
    status_notification = models.StatusNotification(**notification_data)
    status_notification.save()
    notifications.send_simple_front_notification(
        contact_info,
        status_notification.sent_message,
        subject="Update from Clear My Record")
    messages.success(
        request, "Notified {}".format(sub.get_full_name()))
