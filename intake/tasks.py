from celery import shared_task
from django.conf import settings
from django.core import mail
from django.core import management
from requests import request
from project.services.mixpanel_service import get_mixpanel_client
from project.services import logging_service


@shared_task
def log_to_mixpanel(distinct_id, event_name, **data):
    client = get_mixpanel_client()
    divert = getattr(settings, 'DIVERT_REMOTE_CONNECTIONS', False)
    mixpanel_kwargs = dict(
            distinct_id=distinct_id,
            event_name=event_name,
            properties=data)
    if client and not divert:
        client.track(**mixpanel_kwargs)
    logging_service.format_and_log(
        log_type='call_to_mixpanel', **mixpanel_kwargs)


@shared_task
def celery_request(*args, **kwargs):
    if 'auth' in kwargs:
        kwargs['auth'] = tuple(kwargs['auth'])
    request(*args, **kwargs)


@shared_task
def add_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    # note: this is a really bad sign for this code,
    # no reason it should be this complex
    from intake.services import pdf_service
    pdf_service.fill_pdf_for_application(application_id)
    pdf_service.update_pdf_bundle_for_san_francisco()


@shared_task
def remove_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    from intake.services import pdf_service
    pdf_service.rebuild_pdf_bundle_for_removed_application(application_id)


@shared_task
def send_email(*args, **kwargs):
    # This should be fast enough to run in the request
    mail.send_mail(*args, **kwargs)


@shared_task
def alert_admins_if_org_has_unread_applications():
    management.call_command("alert_admins_if_org_has_unread_applications")
