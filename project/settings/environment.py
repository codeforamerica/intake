from project.settings.base import *
import dj_database_url


STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

SECRET_KEY = os.environ.get('SECRET_KEY')

# looks for 'DATABASE_URL' environmental variable
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres@localhost:5432/intake')
}

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
DEFAULT_HOST = os.environ.get('DEFAULT_HOST', 'http://localhost:8000')

# settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('BUCKETEER_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('BUCKETEER_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('BUCKETEER_BUCKET_NAME')

MEDIA_ROOT = ''

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

# Email settings
EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "admin@localhost")
DEFAULT_FROM_EMAIL = MAIL_DEFAULT_SENDER
VOICEMAIL_NOTIFICATION_EMAIL = os.environ.get(
    'VOICEMAIL_NOTIFICATION_EMAIL')

# Twilio API
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# Slack Web hook
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Front API
FRONT_API_TOKEN = os.environ.get("FRONT_API_TOKEN")
FRONT_EMAIL_CHANNEL_ID = os.environ.get("FRONT_EMAIL_CHANNEL_ID")
FRONT_PHONE_CHANNEL_ID = os.environ.get("FRONT_PHONE_CHANNEL_ID")

# Mixpanel Analytics
MIXPANEL_KEY = os.environ.get("MIXPANEL_KEY", "")

# configure django-debug-toolbar
USE_DEBUG_TOOLBAR = os.environ.get('USE_DEBUG_TOOLBAR', 0)

LIVE_COUNTY_CHOICES = os.environ.get('LIVE_COUNTY_CHOICES', False)

CELERY_BROKER_URL = os.environ.get('CLOUDAMQP_URL')

TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD")
