from project.settings.base import *
import dj_database_url

SECRET_KEY = os.environ.get('SECRET_KEY', 'something super secret')

# looks for 'DATABASE_URL' environmental variable
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres@localhost:5432/intake')
}

STATIC_ROOT = os.environ.get('STATIC_ROOT', 
    os.path.join(REPO_DIR, 'project', 'static'))

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', 
    os.path.join(REPO_DIR, 'project', 'media'))

EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
DEFAULT_NOTIFICATION_EMAIL = os.environ.get("DEFAULT_NOTIFICATION_EMAIL")