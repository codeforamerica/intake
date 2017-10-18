from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from intake.exceptions import MailgunAPIError


MAILGUN_EMAIL_VALIDATION_URL = \
    'https://api.mailgun.net/v3/address/private/validate'
MAILGUN_ROUTES_API_URL = 'https://api.mailgun.net/v3/routes'


def mailgun_auth():
    return HTTPBasicAuth(
            'api', getattr(settings, 'MAILGUN_PRIVATE_API_KEY', ''))


def raise_error_if_not_200(status_code, parsed_response):
    if status_code != 200:
        raise MailgunAPIError(
            'Mailgun returned {} {}'.format(
                status_code, parsed_response))


def get_response_status_code_and_content(response):
    if response.content:
        response_json = response.json()
    else:
        response_json = None
    return (response.status_code, response_json)


def mailgun_email_validation_get_request(url, query_params):
    if not getattr(settings, 'VALIDATE_EMAILS_WITH_MAILGUN', False):
        # Don't make external calls to mailgun locally
        return (200, dict(is_valid=True, mailbox_verification='true'))
    response = requests.get(
        url, auth=mailgun_auth(), params=query_params)
    return get_response_status_code_and_content(response)


def validate_email_with_mailgun(email):
    status_code, parsed_response = mailgun_email_validation_get_request(
        MAILGUN_EMAIL_VALIDATION_URL,
        query_params=dict(
            address=email,
            mailbox_verification=True))
    raise_error_if_not_200(status_code, parsed_response)
    is_valid = parsed_response['is_valid']
    # possible return values are 'false', 'unknown', and 'true'
    mailbox_might_exist = parsed_response['mailbox_verification'] != 'false'
    suggestion = parsed_response.get('did_you_mean', None)
    return (is_valid and mailbox_might_exist, suggestion)


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
