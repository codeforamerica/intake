from project.settings.environment import *

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
# settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('BUCKET_NAME')

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

# use mailgun's REST API to validate email addresses
VALIDATE_EMAILS_WITH_MAILGUN = True
