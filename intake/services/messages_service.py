from django.contrib import messages


def flash_errors(request, *errors):
    for error in errors:
        messages.error(request, error)


def flash_success(request, *success_messages):
    for success in success_messages:
        messages.success(request, success)


def flash_warnings(request, *warning_messages):
    for warning in warning_messages:
        messages.warning(request, warning)
