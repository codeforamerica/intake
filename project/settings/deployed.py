from project.settings.environment import *
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

RELEASE_DATETIME = os.environ.get('MANIFEST_VERSION')

INSTALLED_APPS += ['django_celery_beat']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('DATABASE_HOST'),
        'NAME': 'intake',
        'USER': 'intake',
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
    },
    'purged': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('PURGED_DATABASE_HOST'),
        'NAME': 'intake',
        'USER': os.environ.get('PURGED_DATABASE_USER'),
        'PASSWORD': os.environ.get('PURGED_DATABASE_PASSWORD'),
    }
}

CELERY_BROKER_URL = [
    os.environ.get('CLOUDAMQP_URL'),
    os.environ.get('CLOUDAMQP_WHITE_URL'),
]

# AWS Credentials for media files
MEDIA_ROOT = ''
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
CLIPS_DATABASE_ALIAS = 'purged'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True

AWS_DEFAULT_ACL = 'private'  # Keeps things in bucket private
SYNC_AWS_ID = os.environ.get('SYNC_AWS_ID')
SYNC_AWS_KEY = os.environ.get('SYNC_AWS_KEY')
SYNC_BUCKET = os.environ.get('SYNC_BUCKET')
AWS_CLI_LOCATION = os.environ.get('AWS_CLI_LOCATION')
SYNC_FIXTURE_LOCATION = os.environ.get('SYNC_FIXTURE_LOCATION')
ORIGIN_MEDIA_BUCKET_FOR_SYNC = os.environ.get('ORIGIN_MEDIA_BUCKET_FOR_SYNC')

# Local storage for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False

# Use mailgun's REST API to validate email addresses
DIVERT_REMOTE_CONNECTIONS = os.environ.get(
    'DIVERT_REMOTE_CONNECTIONS', 'True') == 'True'
ALLOW_REQUESTS_TO_MAILGUN = not DIVERT_REMOTE_CONNECTIONS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'testlogger': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

# Initialize Sentry
sentry_sdk.init(
    dsn=SENTRY_URL,
    environment=SENTRY_ENVIRONMENT,
    integrations=[
        DjangoIntegration(),
        CeleryIntegration()
    ],

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    #
    # CMR note: Our users are either staff or legal aid (not clients), so
    # sending for now
    send_default_pii=True
)
