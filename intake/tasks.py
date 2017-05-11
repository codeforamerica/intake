from celery import shared_task
from requests import request
from project.services.mixpanel_service import log_to_mixpanel

log_to_mixpanel = shared_task(log_to_mixpanel)


@shared_task
def celery_request(*args, **kwargs):
    request(*args, **kwargs)
