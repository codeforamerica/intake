from collections import namedtuple
import json
import requests
from project.jinja2 import url_with_ids
from django.core import mail
from django.conf import settings
from django.utils.translation import ugettext as _

from django.template import loader, Context

jinja = loader.engines['jinja']


class JinjaNotInitializedError(Exception):
    pass


class DuplicateTemplateError(Exception):
    pass


class FrontAPIError(Exception):
    pass


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
            any_name_at_all_template_path --> loads a template from template dirs
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
        content_keys = []
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
    default_recipients = [settings.DEFAULT_NOTIFICATION_EMAIL]

    def __init__(self, subject_template='', body_template_path=''):
        super().__init__(
            subject_template=subject_template,
            body_template_path=body_template_path
        )

    def send(self, to=None, from_email=None, **context_args):
        content = self.render(**context_args)
        from_email = from_email or self.default_from_email
        to = to or self.default_recipients
        return mail.send_mail(
            subject=content.subject,
            message=content.body,
            from_email=from_email,
            recipient_list=to
        )


class FrontNotification(TemplateNotification):

    def __init__(self, default_context=None, subject_template='',
                 body_template_path=''):
        super().__init__(
            default_context=default_context,
            subject_template=subject_template,
            body_template_path=body_template_path
        )

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

    def raise_post_errors(self, response, payload):
        if response.status_code != 202:
            raise FrontAPIError(
                """
STATUS {status}
Error: {title}
{detail}
REQUEST JSON:
{payload}
""".format(payload=payload, **response.json()['errors'][0]))

    def send(self, to, **context_args):
        content = self.render(**context_args)
        data = {
            'body': content.body.replace('\n', '<br>'),
            'text': content.body,
            'to': to,
            'options': {
                'archive': False
            }
        }
        if hasattr(content, 'subject') and content.subject:
            data['subject'] = content.subject
        payload = json.dumps(data)
        if check_that_remote_connections_are_okay(
                'FRONT POST:', payload):
            result = requests.post(
                url=self.build_api_url_endpoint(),
                data=payload,
                headers=self.build_headers()
            )
            self.raise_post_errors(result, payload)
            return result


class FrontEmailNotification(FrontNotification):
    channel_id = getattr(settings, 'FRONT_EMAIL_CHANNEL_ID', None)


class FrontSMSNotification(FrontNotification):
    channel_id = getattr(settings, 'FRONT_PHONE_CHANNEL_ID', None)


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
            return requests.post(
                url=self.webhook_url,
                data=payload,
                headers=self.headers)


class SlackTemplateNotification(BasicSlackNotification, TemplateNotification):

    def __init__(self, default_context=None,
                 message_template_path='', webhook_url=None):
        BasicSlackNotification.__init__(self, webhook_url)
        TemplateNotification.__init__(self,
                                      default_context=default_context,
                                      message_template_path=message_template_path)

    def render(self, **context_args):
        if 'submissions' in context_args and 'bundle_url' not in context_args:
            bundle_url = getattr(settings, 'DEFAULT_HOST', '') + url_with_ids(
                'intake-app_bundle',
                [s.id for s in context_args['submissions']])
            context_args.update(bundle_url=bundle_url)
        return super().render(**context_args)

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

# count, submission_ids
front_email_daily_app_bundle = FrontEmailNotification(
    subject_template=_(
        "{{current_local_time('%a %b %-d, %Y')}}: Online applications to Clean Slate"),
    body_template_path='email/app_bundle_email.jinja')
email_daily_app_bundle = EmailNotification(
    subject_template=_(
        "{{current_local_time('%a %b %-d, %Y')}}: Online applications to Clean Slate"),
    body_template_path='email/app_bundle_email.jinja')

# submissions, emails
slack_app_bundle_sent = SlackTemplateNotification(
    message_template_path="slack/app_bundle_sent.jinja"
)

# CONFIRMATIONS

# name, staff name
email_confirmation = FrontEmailNotification(
    subject_template=_("Thanks for applying - Next steps"),
    body_template_path='email/confirmation.jinja')
sms_confirmation = FrontSMSNotification(
    body_template_path='text/confirmation.jinja'
)

# submission, method
slack_confirmation_sent = SlackTemplateNotification(
    message_template_path="slack/confirmation_sent.jinja")
# submission, method, errors
slack_confirmation_send_failed = SlackTemplateNotification(
    message_template_path="slack/confirmation_failed.jinja")
