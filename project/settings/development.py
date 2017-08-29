from project.settings.base import *


DIVERT_REMOTE_CONNECTIONS = True

#TEST_PDF_PATH = './cleanslatecombined.pdf'

#CELERY_BROKER_URL = 'amqp://localhost'
CELERY_TASK_ALWAYS_EAGER = True


SECRET_KEY = os.environ.get('SECRET_KEY')
# settings for static files
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
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
# settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('BUCKET_NAME')
