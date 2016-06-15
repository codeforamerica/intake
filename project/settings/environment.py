from project.settings.base import *
import dj_database_url

SECRET_KEY = os.environ.get('SECRET_KEY', 'something super secret')

# looks for 'DATABASE_URL' environmental variable
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres@localhost:5432/intake')
}

# settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE',
    'django.core.files.storage.FileSystemStorage')
# set to 'storages.backends.s3boto.S3BotoStorage' for prod

if 'FileSystem' in DEFAULT_FILE_STORAGE:
    MEDIA_ROOT = os.path.join(REPO_DIR, 'project', 'media')
else:
    MEDIA_ROOT = ''

# static files location
STATIC_ROOT = os.environ.get('STATIC_ROOT', 
    os.path.join(REPO_DIR, 'project', 'static'))


# Email settings
EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "admin@localhost")
DEFAULT_NOTIFICATION_EMAIL = os.environ.get("DEFAULT_NOTIFICATION_EMAIL", "user@localhost")

# Slack Web hook
SLACK_WEBHOOK_URL=os.environ.get("SLACK_WEBHOOK_URL")

# Front API
FRONT_API_TOKEN=os.environ.get("FRONT_API_TOKEN")
FRONT_EMAIL_CHANNEL_ID=os.environ.get("FRONT_EMAIL_CHANNEL_ID")
FRONT_PHONE_CHANNEL_ID=os.environ.get("FRONT_PHONE_CHANNEL_ID")

# Temporary defaults for agencies
DEFAULT_AGENCY_USER_EMAIL = os.environ.get('DEFAULT_AGENCY_USER_EMAIL',
    'clearmyrecord@codeforamerica.org')
