from project.settings.environment import *

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = True
ALLOWED_HOSTS = ['*', ]
database_config = dj_database_url.config(env='TEST_DB_URL')
DATABASES = {
    'default': database_config,
    'TEST': {
        'NAME': database_config['NAME'],
    },
}
