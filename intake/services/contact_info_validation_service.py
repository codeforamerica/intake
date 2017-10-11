from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from intake.exceptions import MailgunAPIError


MAILGUN_EMAIL_VALIDATION_URL = \
    'https://api.mailgun.net/v3/address/private/validate'


def mailgun_get_request(url, query_params):
    if not getattr(settings, 'VALIDATE_EMAILS_WITH_MAILGUN', False):
        # Don't make external calls to mailgun locally
        return (200, dict(is_valid=True, mailbox_verification='true'))
    response = requests.get(
        url,
        auth=HTTPBasicAuth(
            'api', getattr(settings, 'MAILGUN_PRIVATE_API_KEY', '')),
        params=query_params)
    if response.content:
        response_json = response.json()
    else:
        response_json = None
    return (response.status_code, response_json)


def validate_email_with_mailgun(email):
    status_code, parsed_response = mailgun_get_request(
        MAILGUN_EMAIL_VALIDATION_URL,
        query_params=dict(
            address=email,
            mailbox_verification=True))
    if status_code != 200:
        raise MailgunAPIError(
            'Mailgun returned {} {}'.format(
                status_code, parsed_response))
    is_valid = parsed_response['is_valid']
    # possible return values are 'false', 'unknown', and 'true'
    mailbox_might_exist = parsed_response['mailbox_verification'] != 'false'
    suggestion = parsed_response.get('did_you_mean', None)
    return (is_valid and mailbox_might_exist, suggestion)
