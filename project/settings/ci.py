import sys
from project.settings.environment import *
from project.settings.test import *

DEBUG = True
DIVERT_REMOTE_CONNECTIONS = True
INTERNAL_IPS = ['127.0.0.1', '::1']
CELERY_TASK_ALWAYS_EAGER = True
LIVE_COUNTY_CHOICES = False

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_ROOT = os.path.join(REPO_DIR, 'project', 'media')
STATIC_ROOT = os.path.join(REPO_DIR, 'staticfiles')

BROWSER_STACK_ID = os.environ.get('BROWSER_STACK_ID')
BROWSER_STACK_KEY = os.environ.get('BROWSER_STACK_KEY')

# Build Compress with Node Modules
NODE_MODULES_PATH = os.path.join(REPO_DIR, 'node_modules')
COMPRESS_PRECOMPILERS = build_precompilers(NODE_MODULES_PATH)

TEST_USER_PASSWORD = 'cmr-travis'
PARTNERSHIPS_LEAD_INBOX = "cmrtestuser@gmail.com"

CLIPS_DATABASE_ALIAS = 'default'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'intake',
        'USER': 'postgres',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'project': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
