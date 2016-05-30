from django.core import mail
from django.conf import settings

from django.template.loader import get_template
from project.jinja2 import jinja_config as jinja
from django.template import Context

class JinjaNotInitializedError(Exception):
    pass

class EmailNotification:
    
    default_from_email = settings.MAIL_DEFAULT_SENDER
    default_recipients = [settings.DEFAULT_NOTIFICATION_EMAIL]

    def __init__(self, subject_template='', body_template_path=''):
        self.subject_template_str = subject_template
        self.body_template_path = body_template_path
        self.subject_template = None
        self.body_template = None

    def build_templates(self):
        if not jinja.env:
            raise JinjaNotInitializedError("the jinja environment has not been initialized")
        self.subject_template = jinja.env.from_string(self.subject_template_str)
        self.body_template = get_template(self.body_template_path)


    def send(self, to=None, from_email=None, **context_args):
        if not self.body_template or not self.subject_template:
            self.build_templates()
        from_email = from_email or self.default_from_email
        to = to or self.default_recipients
        if isinstance(to, str):
            to = [to]
        mail.send_mail(
            subject=self.subject_template.render(context_args),
            message=self.body_template.render(context_args),
            from_email=from_email,
            recipient_list=to
            )

new_submission_email = EmailNotification(
    '''New application to {{ request.build_absolute_uri(url('intake-apply')) }} received {{ 
        submission.get_local_date_received("%-m/%-d/%Y %-I:%M %p %Z") 
        }}''',
    "notification_email.txt"
    )

submission_viewed_email = EmailNotification(
    'Application {{ submission.id }} viewed by {{ user.email }}',
    "submission_viewed_email.txt"
    )

