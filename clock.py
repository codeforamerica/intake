import os
from celery.schedules import crontab

from project.celery import app

day_of_month = os.environ.get('UNREAD_NOTIFICATIONS_DAY_OF_MONTH', 1)
hour = os.environ.get('UNREAD_NOTIFICATIONS_HOUR', 23)
minute = os.environ.get('UNREAD_NOTIFICATIONS_MINUTE', 0)

app.conf.beat_schedule = {
    # Executes first of every month
    'send-notifications-every-month': {
        'task': 'intake.tasks.alert_admins_if_org_has_unread_applications',
        'schedule': crontab(hour=hour, minute=minute, day_of_month=day_of_month)
    },
}
app.conf.timezone = 'US/Pacific'
