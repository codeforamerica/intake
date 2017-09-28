from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from intake.exceptions import MailgunAPIError


MAILGUN_EMAIL_VALIDATION_URL = \
    'https://api.mailgun.net/v3/address/private/validate'


def validate_email_with_mailgun(email):
    response = requests.get(
            MAILGUN_EMAIL_VALIDATION_URL,
            auth=HTTPBasicAuth(
                'api', getattr(settings, 'MAILGUN_PRIVATE_API_KEY', '')),
            params=dict(
                address=email,
                mailbox_verification=True))
    if response.status_code != 200:
        raise MailgunAPIError(
            'Mailgun returned {} {}'.format(
                response.status_code, response.reason))
    parsed_response = response.json()
    is_valid = parsed_response['is_valid']
    mailbox_exists = parsed_response['mailbox_verification'] == 'true'
    suggestion = parsed_response.get('did_you_mean', None)
    return (is_valid and mailbox_exists, suggestion)
