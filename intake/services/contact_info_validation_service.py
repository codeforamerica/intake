from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from intake.exceptions import MailgunAPIError


MAILGUN_EMAIL_VALIDATION_URL = \
    'https://api.mailgun.net/v3/address/private/validate'


def mailgun_get_request(url, query_params):
    response = requests.get(
        url,
        auth=HTTPBasicAuth(
            'api', getattr(settings, 'MAILGUN_PRIVATE_API_KEY', '')),
        params=query_params)
    return (response.status_code, response.json())


def validate_email_with_mailgun(email):
    raise Exception('calling validate mailgun')
    status_code, parsed_response = mailgun_get_request(
        MAILGUN_EMAIL_VALIDATION_URL,
        query_params=dict(
            address=email,
            mailbox_verification=True))
    if status_code != 200:
        raise MailgunAPIError(
            'Mailgun returned {} {}'.format(
                status_code, response.reason))
    is_valid = parsed_response['is_valid']
    mailbox_exists = parsed_response['mailbox_verification'] == 'true'
    suggestion = parsed_response.get('did_you_mean', None)
    return (is_valid and mailbox_exists, suggestion)
