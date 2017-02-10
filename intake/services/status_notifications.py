from django.contrib import messages
from intake import models, notifications
import intake.services.submissions as SubmissionsService
from django.template import loader

jinja = loader.engines['jinja']


def build_status_notification_context(status_update_data):
    org = status_update_data['application'].organization
    return dict(
        organization=org.name,
        county=org.county.name + ' County',
    )


def render_template_option(template_string, context):
    template = jinja.env.from_string(template_string)
    return template.render(context)


def get_notification_intro(profile):
    return "Clear My Record update from {} at {}:".format(
        profile.name, profile.organization.name)


def get_base_message_from_status_update_data(status_update_data):
    template_option_context = \
        build_status_notification_context(status_update_data)
    status_type_message = render_template_option(
        status_update_data['status_type'].template,
        template_option_context)
    next_step_message = ' '.join([
        render_template_option(
            next_step.template,
            template_option_context)
        for next_step in status_update_data.get('next_steps', [])])
    other_next_step = status_update_data.get('other_next_step')
    if other_next_step:
        next_step_message += (' ' + other_next_step)
    return ' '.join([
        status_type_message, status_update_data['additional_information'],
        next_step_message])


def get_status_update_success_message(sub, status_type):
    return 'Updated status to "{}" for {}'.format(
        status_type.display_name, sub.get_full_name())


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
    full_message = '/n/n'.join([
        get_notification_intro(status_update.author.profile),
        status_notification.sent_message])
    notifications.send_simple_front_notification(
        contact_info, full_message,
        subject="Update from Clear My Record")
    success_message = get_status_update_success_message(
            sub, status_update.status_type)
    messages.success(request, success_message)
