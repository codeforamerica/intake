from collections import namedtuple
import json
import requests

from django.core import mail
from django.conf import settings

from django.template.loader import get_template
from project.jinja2 import jinja_config as jinja
from django.template import Context


class JinjaNotInitializedError(Exception):
    pass


class DuplicateTemplateError(Exception):
    pass


class FrontAPIError(Exception):
    pass


class BaseNotification:

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
            self.templates[key] = get_template(string)

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
            raise JinjaNotInitializedError("the jinja environment has not been initialized")
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



class EmailNotification(BaseNotification):
    
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
        if isinstance(to, str):
            to = [to]
        return mail.send_mail(
            subject=content.subject,
            message=content.body,
            from_email=from_email,
            recipient_list=to
            )

class FrontNotification(BaseNotification): 

    def __init__(self, default_context=None, subject_template='', body_template_path=''):
        super().__init__(
            default_context=default_context,
            subject_template=subject_template,
            body_template_path=body_template_path
            )

    def build_headers(self):
        return {
            'Authorization': 'Bearer {}'.format(
                settings.FRONT_API_TOKEN),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def build_api_url_endpoint(self):
        root_url = 'https://api2.frontapp.com/channels/{}/messages'
        return root_url.format(self.channel_id)

    def raise_post_errors(self, response):
        if response.status_code != 202:
            raise FrontAPIError(
"""
STATUS {status}
Error: {title}
{detail}
""".format(**response.json()['errors'][0]))

    def send(self, to, **context_args):
        content = self.render(**context_args)
        data = {
            'body': content.body,
            'to': to,
            'options': {
                'archive': False
                }
            }
        if hasattr(content, 'subject') and content.subject:
            data['subject'] = content.subject
        payload = json.dumps(data)
        result = requests.post(
            url=self.build_api_url_endpoint(),
            data=payload,
            headers=self.build_headers()
            )
        self.raise_post_errors(result)
        return result



class FrontEmailNotification(FrontNotification):
    channel_id = settings.FRONT_EMAIL_CHANNEL_ID


class FrontSMSNotification(FrontNotification):
    channel_id = settings.FRONT_PHONE_CHANNEL_ID


class SlackNotification(BaseNotification):

    def __init__(self, default_context=None, message_template_path='', webhook_url=None):
        super().__init__(
            default_context=default_context,
            message_template_path=message_template_path)
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    def escape(self, text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def send(self, webhook_url=None, **context_args):
        content = self.render(**context_args)
        payload = json.dumps({
            'text': self.escape(content.message)
        })
        headers = {'Content-type': 'application/json'}
        return requests.post(
            webhook_url,
            data=payload,
            headers=headers)


# submission, submission_count, request
slack_new_submission = SlackNotification(
    message_template_path="new_submission.slack")

# submissions, user
slack_submissions_viewed = SlackNotification(
    {'action': 'opened'},
    message_template_path="bundle_action.slack")

# submissions, user
slack_submissions_processed = SlackNotification(
    {'action': 'processed'},
    message_template_path="bundle_action.slack")

# submissions, user
slack_submissions_deleted = SlackNotification(
    {'action': 'deleted'},
    message_template_path="bundle_action.slack")

# count, request, submission_ids
front_email_daily_app_bundle = FrontEmailNotification(
    subject_template="{{current_local_time('%a %b %-d, %Y')}}: Online applications to Clean Slate",
    body_template_path='app_bundle_email.txt')
