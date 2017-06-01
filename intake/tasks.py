from celery import shared_task
from requests import request
import intake.services.pdf_service as PDFService


@shared_task
def celery_request(*args, **kwargs):
    request(*args, **kwargs)


@shared_task
def add_application_pdfs(application_id):
    PDFService.fill_pdf_for_application(application_id)
    PDFService.rebuild_newapps_pdf_for_new_application(application_id)


@shared_task
def remove_application_pdfs(application_id):
    PDFService.rebuild_newapps_pdf_for_removed_application(application_id)
