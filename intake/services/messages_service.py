from django.contrib import messages


def flash_errors(request, *errors):
    for error in errors:
        messages.error(request, error)
