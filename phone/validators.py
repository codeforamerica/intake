from twilio.request_validator import RequestValidator
from django.conf import settings


def is_valid_twilio_request(request):
    twilio_request_validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    request_path = request.build_absolute_uri(
        request.get_full_path()).replace('http:', 'https:')
    # trailing slashes should be removed
    if request_path[-1] == '/':
        request_path = request_path[:-1]
    twilio_signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
    return twilio_request_validator.validate(
            request_path, request.POST, twilio_signature)
