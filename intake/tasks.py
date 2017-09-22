from django.core import mail
from django.conf import settings
from requests import request
from zappa.async import task
from project.services.mixpanel_service import get_mixpanel_client
from project.services import logging_service
from celery import shared_task


@task
def debug_task(string):
    print('Request: {0!r}'.format(string))


@task
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


@task
def celery_request(*args, **kwargs):
    request(*args, **kwargs)


@task
def add_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    # note: this is a really bad sign for this code,
    # no reason it should be this complex
    import intake.services.pdf_service as PDFService
    PDFService.fill_pdf_for_application(application_id)
    PDFService.update_pdf_bundle_for_san_francisco()


@task
def remove_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    import intake.services.pdf_service as PDFService
    PDFService.rebuild_pdf_bundle_for_removed_application(application_id)


@task
def send_email(*args, **kwargs):
    # This should be fast enough to run in the request
    mail.send_mail(*args, **kwargs)
