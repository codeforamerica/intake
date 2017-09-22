from project.settings.base import *


DIVERT_REMOTE_CONNECTIONS = True

#TEST_PDF_PATH = './cleanslatecombined.pdf'

#CELERY_BROKER_URL = 'amqp://localhost'
CELERY_TASK_ALWAYS_EAGER = True


SECRET_KEY = os.environ.get('SECRET_KEY')
# settings for static files
# settings for media files
MEDIA_ROOT = ''
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

MAIL_DEFAULT_SENDER = "admin@localhost"
DEFAULT_NOTIFICATION_EMAIL = "user@localhost"
PARTNERSHIPS_LEAD_INBOX = 'anotheremail@example.space'

TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD')

VOICEMAIL_NOTIFICATION_EMAIL = 'mikela@codeforamerica.org'

USE_DEBUG_TOOLBAR = False
DEBUG = True
ALLOWED_HOSTS = ['*']

# looks for 'DATABASE_URL' environmental variable
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
LIVE_COUNTY_CHOICES = False

COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# settings for media file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = 'cmr-development-r1-static-files'
# settings for static files
STATIC_BUCKET = 'cmr-development-r1-static-files'
COMPRESS_URL = 'https://%s.s3.amazonaws.com/' % STATIC_BUCKET
STATIC_URL = COMPRESS_URL
STATICFILES_LOCATION = 'static'  # location in bucket TODO: remove
STATICFILES_STORAGE = 'project.custom_storages.CachedS3BotoStorage'


COMPRESS_ROOT = os.path.join(REPO_DIR, 'staticfiles')
COMPRESS_STORAGE = STATICFILES_STORAGE

AWS_QUERYSTRING_AUTH = False
