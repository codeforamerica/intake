from django.contrib import messages


def flash_errors(request, *errors):
    for error in errors:
        messages.error(request, error)


def flash_success(request, *sucess_messages):
    for success in sucess_messages:
        messages.success(request, success)
