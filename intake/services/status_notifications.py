import Levenshtein
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.template import loader
from django.urls import reverse
from intake import models, notifications


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
    greeting_template = _("Clear My Record update from {person} at {org}")
    return greeting_template.format(
        person=profile.name,
        org=profile.organization.name)


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
    if next_step_message:
        next_step_message = ' '.join([
            'Here are your next steps:', next_step_message
        ])
    return ' '.join([
        status_type_message, status_update_data['additional_information'],
        next_step_message])


def get_status_update_success_message(full_name, status_type):
    return 'Updated status to "{}" for {}'.format(
        status_type.display_name, full_name)


def save_and_send_status_notification(
        request, notification_data, status_update):
    """Called by send_and_save_new_status,

    Responsible for the 'notification'portion of a status update.
    """
    sub = status_update.application.form_submission
    contact_info = sub.get_usable_contact_info()
    author_profile = status_update.author.profile
    notification_intro = get_notification_intro(author_profile)
    status_update_data = vars(status_update)
    status_update_data.update(
        author=status_update.author,
        status_type=status_update.status_type,
        application=status_update.application,
        next_steps=list(status_update.next_steps.all()))
    default_message = '\n\n'.join([
        notification_intro,
        get_base_message_from_status_update_data(request, status_update_data)
    ])
    edited_message = '\n\n'.join([
        notification_intro,
        notification_data['sent_message']])
    notification_data.update(
        base_message=default_message,
        sent_message=edited_message,
        status_update=status_update,
        contact_info=contact_info)
    status_notification = models.StatusNotification(**notification_data)
    status_notification.save()
    notifications.send_applicant_notification(
        contact_info, edited_message,
        subject="Update from Clear My Record",
        sender_profile=author_profile)


def send_and_save_new_status(request, notification_data, status_update_data):
    next_steps = status_update_data.pop('next_steps', [])
    status_update = models.StatusUpdate(**status_update_data)
    status_update.save()
    status_update.next_steps.add(*next_steps)
    save_and_send_status_notification(
        request, notification_data, status_update)
    success_message = get_status_update_success_message(
        status_update.application.form_submission.get_full_name(),
        status_update.status_type)
    messages.success(request, success_message)
    return status_update


def get_message_change_ratio(status_update):
    """Expects a status update instance, returns a number representing
    how much a message has been edited (1.0 completely changed, 0.0 unchanged)
    based on Levenshtein ratio.
    If a status update has no associated notification, returns None
    https://github.com/ztane/python-Levenshtein
    """
    if hasattr(status_update, 'notification'):
        author_profile = status_update.author.profile
        intro_text = get_notification_intro(author_profile) + '\n\n'
        return 1.0 - Levenshtein.ratio(
            *[message.replace(intro_text, '')
              for message in (
                status_update.notification.base_message,
                status_update.notification.sent_message)])
    else:
        return None


def get_contact_info_keys(status_update):
    """Returns the contact info method keys (email, sms)
    used to send a notification for a status update if the notification
    exists. Returns [] if there is no notification
    """
    if hasattr(status_update, 'notification'):
        return list(status_update.notification.contact_info.keys())
    else:
        return []


def has_unsent_additional_info(status_update):
    if hasattr(status_update, 'notification'):
        if len(status_update.additional_information) > 1:
            return (status_update.additional_information in
                    status_update.notification.sent_message)


def has_unsent_other_next_step(status_update):
    if hasattr(status_update, 'notification'):
        if len(status_update.other_next_step) > 1:
            return (status_update.other_next_step in
                    status_update.notification.sent_message)
