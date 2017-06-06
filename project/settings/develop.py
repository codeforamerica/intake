from project.settings.prod import *

DEBUG = False
ALLOWED_HOSTS = ['*']

COMPRESS_OFFLINE = False
CELERY_TASK_ALWAYS_EAGER = True