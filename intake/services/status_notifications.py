from django.contrib import messages
from intake import models, notifications
import intake.services.submissions as SubmissionsService
from django.template import loader
from django.core.urlresolvers import reverse

jinja = loader.engines['jinja']


def build_status_notification_context(request, status_update_data):
    org = status_update_data['application'].organization
    return dict(
        organization_contact_message=org.get_contact_info_message(),
        county=org.county.name + ' County',
        personal_statement_link=request.build_absolute_uri(
            reverse('intake-personal_statement')),
        letters_of_rec_link=request.build_absolute_uri(
            reverse('intake-recommendation_letters'))
    )


def get_notification_intro(profile):
    return "Clear My Record update from {} at {}:".format(
        profile.name, profile.organization.name)


def get_base_message_from_status_update_data(request, status_update_data):
    template_option_context = \
        build_status_notification_context(request, status_update_data)
    status_type_message = status_update_data['status_type'].render(
        template_option_context)
    next_step_message = ' '.join([
        next_step.render(template_option_context)
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
            request, status_update_data),
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
