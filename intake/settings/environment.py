import os
from intake.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'intake',
        'USER': os.environ['DATABASE_USER'],
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
    }
}

STATIC_ROOT = os.environ['STATIC_ROOT']
MEDIA_ROOT = os.environ['MEDIA_ROOT']