from celery import shared_task
from project.external_services import log_to_mixpanel


log_to_mixpanel = shared_task(log_to_mixpanel)
