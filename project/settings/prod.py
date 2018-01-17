from project.settings.environment import *

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

# AWS Credentials for Static Files
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('STATIC_BUCKET')
# settings for media files
MEDIA_ROOT = ''
DEFAULT_FILE_STORAGE = 'project.custom_storages.MediaStorage'
MEDIA_BUCKET = os.environ.get('MEDIA_BUCKET')
# settings for static files
COMPRESS_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = COMPRESS_URL
STATICFILES_STORAGE = 'project.custom_storages.CachedS3BotoStorage'
COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
COMPRESS_ROOT = os.path.join(REPO_DIR, 'staticfiles-cache')
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_OFFLINE_MANIFEST = 'manifest.%s.json' % RELEASE_DATETIME
AWS_S3_FILE_OVERWRITE = True
AWS_QUERYSTRING_AUTH = False  # For Static only We override in MediaStorage
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

RAVEN_CONFIG = {
    'dsn': 'https://<key>:<secret>@sentry.io/<project>',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': RELEASE_DATETIME,
}
MIDDLEWARE = (
    'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
) + MIDDLEWARE

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        'sentry': {
            'level': 'INFO',
            'class':
            'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
    },
    'loggers': {
        'project': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
        },
    },
}
