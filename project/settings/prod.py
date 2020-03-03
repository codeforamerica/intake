from project.settings.environment import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

RELEASE_DATETIME = os.environ.get('MANIFEST_VERSION')

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
CLIPS_DATABASE_ALIAS = 'purged'

# AWS Credentials for media files
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
MEDIA_ROOT = ''
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = os.environ.get('MEDIA_BUCKET')
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True

AWS_DEFAULT_ACL = 'private'  # Keeps things in bucket private
SYNC_AWS_ID = os.environ.get('SYNC_AWS_ID')
SYNC_AWS_KEY = os.environ.get('SYNC_AWS_KEY')
SYNC_BUCKET = os.environ.get('SYNC_BUCKET')
AWS_CLI_LOCATION = os.environ.get('AWS_CLI_LOCATION')
SYNC_FIXTURE_LOCATION = os.environ.get('SYNC_FIXTURE_LOCATION')
ORIGIN_MEDIA_BUCKET_FOR_SYNC = os.environ.get('ORIGIN_MEDIA_BUCKET_FOR_SYNC')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False
# hides counties where none of the orgs are officially live
LIVE_COUNTY_CHOICES = True

DIVERT_REMOTE_CONNECTIONS = os.environ.get(
    'DIVERT_REMOTE_CONNECTIONS', 'True') == 'True'
ALLOW_REQUESTS_TO_MAILGUN = not DIVERT_REMOTE_CONNECTIONS

# Initialize Sentry
sentry_sdk.init(
    dsn=SENTRY_URL,
    integrations=[DjangoIntegration()],

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    #
    # CMR note: Our users are either staff or legal aid (not clients), so
    # sending for noe
    send_default_pii=True
)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
