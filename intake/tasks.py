from celery import shared_task
from django.core import mail
from requests import request
from project.services.mixpanel_service import log_to_mixpanel


log_to_mixpanel = shared_task(log_to_mixpanel)


@shared_task
def celery_request(*args, **kwargs):
    if 'auth' in kwargs:
        kwargs['auth'] = tuple(kwargs['auth'])
    request(*args, **kwargs)


@shared_task
def add_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    import intake.services.pdf_service as PDFService
    PDFService.fill_pdf_for_application(application_id)
    PDFService.update_pdf_bundle_for_san_francisco()


@shared_task
def remove_application_pdfs(application_id):
    # imports of intake services should be called inside of tasks to prevent
    # circular imports
    import intake.services.pdf_service as PDFService
    PDFService.rebuild_pdf_bundle_for_removed_application(application_id)


@shared_task
def send_email(*args, **kwargs):
    mail.send_mail(*args, **kwargs)
