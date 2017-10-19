import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from pprint import pformat
from intake import tasks
from intake.exceptions import MailgunAPIError
from project.decorators import run_if_setting_true

MAILGUN_EMAIL_VALIDATION_URL = \
    'https://api.mailgun.net/v3/address/private/validate'
MAILGUN_ROUTES_API_URL = 'https://api.mailgun.net/v3/routes'
MAILGUN_MESSAGES_API_URL = \
    'https://api.mailgun.net/v3/clearmyrecord.org/messages'


def mailgun_auth():
    return HTTPBasicAuth(
            'api', getattr(settings, 'MAILGUN_PRIVATE_API_KEY', ''))


def raise_error_if_not_200(status_code, parsed_response):
    if status_code != 200:
        msg = 'Domain: {}\n'.format(settings.DEFAULT_HOST)
        msg += 'Mailgun returned status {}\n'.format(status_code)
        msg += 'Response Body: {}\n'.format(
                status_code, pformat(parsed_response, indent=2))
        raise MailgunAPIError(msg)


def get_response_status_code_and_content(response):
    if response.content:
        response_json = response.json()
    else:
        response_json = None
    return response.status_code, response_json


@run_if_setting_true(
    'ALLOW_REQUESTS_TO_MAILGUN',
    (200, dict(is_valid=True, mailbox_verification='true')))
def mailgun_get_request(url, query_params):
    response = requests.get(
        url, auth=mailgun_auth(), params=query_params)
    return get_response_status_code_and_content(response)


def validate_email_with_mailgun(email):
    status_code, parsed_response = mailgun_get_request(
        MAILGUN_EMAIL_VALIDATION_URL,
        query_params=dict(
            address=email,
            mailbox_verification=True))
    raise_error_if_not_200(status_code, parsed_response)
    is_valid = parsed_response['is_valid']
    # possible return values are 'false', 'unknown', and 'true'
    mailbox_might_exist = parsed_response['mailbox_verification'] != 'false'
    suggestion = parsed_response.get('did_you_mean', None)
    return (is_valid and mailbox_might_exist), suggestion


@run_if_setting_true('ALLOW_REQUESTS_TO_MAILGUN', {})
def set_route_for_user_profile(user_profile):
    """Adds a mailgun route to forward incoming emails to given user's email"""
    post_data = {
        'priority': 0,
        'expression': 'match_recipient("{}")'.format(
            user_profile.get_clearmyrecord_email()),
        'action': 'forward("{}")'.format(user_profile.user.email)
    }
    response = requests.post(
        MAILGUN_ROUTES_API_URL, auth=mailgun_auth(), data=post_data)
    status_code, parsed_response = \
        get_response_status_code_and_content(response)
    raise_error_if_not_200(status_code, parsed_response)
    return parsed_response


@run_if_setting_true('ALLOW_REQUESTS_TO_MAILGUN', {})
def send_mailgun_email(to, message, sender_profile, subject):
    post_data = {
        "from": "{name} <{email}>".format(
            name=sender_profile.name,
            email=sender_profile.get_clearmyrecord_email()),
        "to": [to],
        "subject": subject,
        "text": message
    }
    tasks.celery_request.delay(
        'POST', MAILGUN_MESSAGES_API_URL, auth=mailgun_auth(), data=post_data)
