import logging
from django.core import management


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_unopened_apps_notification():
    logger.info('Running Scheduled send unopened apps notification')
    management.call_command('send_unopened_apps_notification')


def send_followups():
    logger.info('Running Scheduled send followups')
    management.call_command('send_followups')


def debug_task():
    logger.info('Running Scheduled debug task')
    management.call_command('debug_task')
