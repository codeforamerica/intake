from project.settings.environment import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('DATABASE_HOST'),
        'NAME': 'intake',
        'USER': 'intake',
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
    }
    'purged': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('PURGED_DATABASE_HOST'),
        'NAME': 'intake',
        'USER': os.environ.get('PURGED_DATABASE_USER'),
        'PASSWORD': os.environ.get('PURGED_DATABASE_PASSWORD'),
    }
}

# settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('BUCKET_NAME')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False
