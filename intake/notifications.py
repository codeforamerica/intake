from collections import namedtuple
import json
from django.core import mail
from django.conf import settings
from django.utils.translation import ugettext as _
from django.template import loader

from intake.constants import SMS, EMAIL
from intake.exceptions import (
    JinjaNotInitializedError,
    DuplicateTemplateError,
    FrontAPIError
)
from intake.tasks import celery_request

jinja = loader.engines['jinja']


def check_that_remote_connections_are_okay(*output_if_not_okay):
    if getattr(settings, 'DIVERT_REMOTE_CONNECTIONS', False):
        print(*output_if_not_okay)
        return False
    else:
        getattr(settings, 'FRONT_API_TOKEN')
        getattr(settings, 'FRONT_EMAIL_CHANNEL_ID')
        getattr(settings, 'FRONT_PHONE_CHANNEL_ID')
        getattr(settings, 'SLACK_WEBHOOK_URL')
    return True


class TemplateNotification:

    def __init__(self, default_context=None, **template_and_path_args):
        '''Feed this init function a set of templates of the form:
            any_name_at_all_template_path --> loads template from template dirs
            any_name_at_all_template --> loads a template from a string
        '''
        self.template_and_path_args = template_and_path_args
        self.templates = {}
        self.default_context = default_context or {}
        self._content_base = None

    def set_template(self, key, string='', from_string=False):
        if key in self.templates:
            raise DuplicateTemplateError(
                "'{}' is already an assigned template".format(key))
        if not string:
            return string
        if from_string:
            self.templates[key] = jinja.env.from_string(string)
        else:
            self.templates[key] = loader.get_template(string)

    def get_context(self, context_dict):
        context = self.default_context
        context.update(context_dict)
        return context

    def _render_template(self, template, context_dict):
        if not hasattr(template, 'render'):
            return template
        return template.render(self.get_context(context_dict))

    def init_templates(self):
        if not jinja.env:
            raise JinjaNotInitializedError(
                "the jinja environment has not been initialized")
        for key, value in self.template_and_path_args.items():
            pieces = key.split('_')
            if pieces[-1] == 'path' and pieces[-2] == 'template':
                built_key = '_'.join(pieces[:-2])
                self.set_template(built_key, value)
            elif pieces[-1] == 'template':
                built_key = '_'.join(pieces[:-1])
                self.set_template(built_key, value, from_string=True)
        self._content_base = namedtuple('RenderedContent',
                                        self.templates.keys())

    def render(self, **context_args):
        if not self.templates:
            self.init_templates()
        return self._content_base(**{
            key: self._render_template(template, context_args)
            for key, template in self.templates.items()
        })

    def render_content_fields(self, **context_args):
        content = self.render(**context_args)
        return '\n\n'.join([
            "{}:\n{}".format(fragment, getattr(content, fragment))
            for fragment in content._fields])


class EmailNotification(TemplateNotification):

    default_from_email = settings.MAIL_DEFAULT_SENDER

    def __init__(self, subject_template='', body_template_path=''):
        super().__init__(
            subject_template=subject_template,
            body_template_path=body_template_path
        )

    def send(self, to=None, from_email=None, **context_args):
        content = self.render(**context_args)
        from_email = from_email or self.default_from_email
        # does not need to check for remote connection permission because
        # emails are diverted by default in a test environment.
        return mail.send_mail(
            subject=content.subject,
            message=content.body,
            from_email=from_email,
            recipient_list=to
        )


class SimpleFrontNotification:

    def __init__(self, channel_id=None):
        if channel_id:
            self.channel_id = channel_id

    def build_headers(self):
        return {
            'Authorization': 'Bearer {}'.format(
                getattr(settings, 'FRONT_API_TOKEN', None)),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def build_api_url_endpoint(self):
        root_url = 'https://api2.frontapp.com/channels/{}/messages'
        return root_url.format(self.channel_id)

    def send(self, to, body, subject=None):
        if isinstance(to, str):
            to = [to]
        data = {
            'body': body.replace('\n', '<br>'),
            'text': body,
            'to': to,
            'options': {
                'archive': True
            }
        }
        if subject:
            data.update(subject=subject)
        payload = json.dumps(data)
        if check_that_remote_connections_are_okay(
                'FRONT POST:', payload):
            celery_request.delay('POST',
                                 url=self.build_api_url_endpoint(),
                                 data=payload,
                                 headers=self.build_headers()
                                 )


class FrontNotification(TemplateNotification, SimpleFrontNotification):

    def __init__(self, default_context=None, subject_template='',
                 body_template_path=''):
        super().__init__(
            default_context=default_context,
            subject_template=subject_template,
            body_template_path=body_template_path
        )

    def send(self, to, **context_args):
        content = self.render(**context_args)
        kwargs = dict(body=content.body)
        if hasattr(content, 'subject') and content.subject:
            kwargs['subject'] = content.subject
        return super().send(to, **kwargs)


class FrontEmailNotification(FrontNotification):
    channel_id = getattr(settings, 'FRONT_EMAIL_CHANNEL_ID', None)


class FrontSMSNotification(FrontNotification):
    channel_id = getattr(settings, 'FRONT_PHONE_CHANNEL_ID', None)


front_sms = SimpleFrontNotification(
    channel_id=getattr(settings, 'FRONT_PHONE_CHANNEL_ID', None))

front_email = SimpleFrontNotification(
    channel_id=getattr(settings, 'FRONT_EMAIL_CHANNEL_ID', None))


def send_simple_front_notification(contact_info, message, subject=None):
    results = []
    if SMS in contact_info:
        results.append(
            front_sms.send(contact_info[SMS], message))
    if EMAIL in contact_info:
        results.append(
            front_email.send(contact_info[EMAIL], message, subject=subject))
    return results


class BasicSlackNotification:

    headers = {'Content-type': 'application/json'}

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or getattr(
            settings, 'SLACK_WEBHOOK_URL', None)

    def send(self, message_text):
        payload = json.dumps({
            'text': message_text
        })
        if check_that_remote_connections_are_okay(
                'SLACK POST:', payload):
            celery_request.delay('POST',
                                 url=self.webhook_url,
                                 data=payload,
                                 headers=self.headers)


class SlackTemplateNotification(BasicSlackNotification, TemplateNotification):

    def __init__(self, default_context=None,
                 message_template_path='', webhook_url=None):
        BasicSlackNotification.__init__(self, webhook_url)
        TemplateNotification.__init__(
            self, default_context=default_context,
            message_template_path=message_template_path)

    def send(self, **context_args):
        content = self.render(**context_args)
        super().send(message_text=content.message)


slack_simple = BasicSlackNotification()

# submission, submission_count, request
slack_new_submission = SlackTemplateNotification(
    message_template_path="slack/new_submission.jinja")

# submissions, user
slack_submissions_viewed = SlackTemplateNotification(
    {'action': 'opened'},
    message_template_path="slack/bundle_action.jinja")

# submissions, user
slack_submissions_processed = SlackTemplateNotification(
    {'action': 'processed'},
    message_template_path="slack/bundle_action.jinja")

# submissions, user
slack_submissions_deleted = SlackTemplateNotification(
    {'action': 'deleted'},
    message_template_path="slack/bundle_action.jinja")

# submission, user
slack_submission_transferred = SlackTemplateNotification(
    {'action': 'transferred'},
    message_template_path="slack/submission_action.jinja")

# count, bundle, bundle_url, app_index_url
front_email_daily_app_bundle = FrontEmailNotification(
    subject_template=_(
        "{{current_local_time('%a %b %-d, %Y')}}: "
        "Online applications to Clear My Record"),
    body_template_path='email/app_bundle_email.jinja')
email_daily_app_bundle = EmailNotification(
    subject_template=_(
        "{{current_local_time('%a %b %-d, %Y')}}: "
        "Online applications to Clear My Record"),
    body_template_path='email/app_bundle_email.jinja')

# submissions, emails
slack_app_bundle_sent = SlackTemplateNotification(
    message_template_path="slack/app_bundle_sent.jinja"
)

# CONFIRMATIONS & FOLLOWUPS

CONFIRMATION_SUBJECT = _("Thanks for applying - Next steps")
# name, staff_name, county_names, next_steps, organizations
email_confirmation = FrontEmailNotification(
    subject_template=CONFIRMATION_SUBJECT,
    body_template_path='email/confirmation.jinja')
sms_confirmation = FrontSMSNotification(
    body_template_path='text/confirmation.jinja'
)

# name, staff_name, followup_messages, county_names, organization_names
email_followup = FrontEmailNotification(
    subject_template=CONFIRMATION_SUBJECT,
    body_template_path='email/followup.jinja')
sms_followup = FrontSMSNotification(
    body_template_path='text/followup.jinja')


# submission, method
slack_notification_sent = SlackTemplateNotification(
    message_template_path="slack/notification_sent.jinja")
# submission, method, errors
slack_notification_failed = SlackTemplateNotification(
    message_template_path="slack/notification_failed.jinja")
