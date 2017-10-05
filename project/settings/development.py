from project.settings.base import *


DIVERT_REMOTE_CONNECTIONS = True

CELERY_TASK_ALWAYS_EAGER = True


SECRET_KEY = os.environ.get('SECRET_KEY')
# settings for static files
# settings for media files
MAIL_DEFAULT_SENDER = "admin@localhost"
DEFAULT_NOTIFICATION_EMAIL = "user@localhost"
PARTNERSHIPS_LEAD_INBOX = 'anotheremail@example.space'

TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD')

VOICEMAIL_NOTIFICATION_EMAIL = 'mikela@codeforamerica.org'

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


MEDIA_ROOT = ''
DEFAULT_FILE_STORAGE = 'project.custom_storages.MediaStorage'
MEDIA_BUCKET = os.environ.get('MEDIA_BUCKET')
COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# settings for media file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('STATIC_BUCKET')
# settings for static files
COMPRESS_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = COMPRESS_URL
STATICFILES_STORAGE = 'project.custom_storages.CachedS3BotoStorage'

COMPRESS_ROOT = os.path.join(REPO_DIR, 'staticfiles-cache')
COMPRESS_STORAGE = STATICFILES_STORAGE


AWS_QUERYSTRING_AUTH = False
