from project.settings.base import *

SECRET_KEY = os.environ.get('SECRET_KEY', 'something super secret')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'intake',
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
    }
}
