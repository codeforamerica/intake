from django.core import management


def send_unopened_apps_notification():
    management.call_command('send_unopened_apps_notification')


def send_followups():
    management.call_command('send_followups')
