import os
from django_jinja.builtins import DEFAULT_EXTENSIONS

REPO_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

ALLOWED_HOSTS = []


DEBUG_TOOLBAR_PATCH_SETTINGS = False
INSTALLED_APPS = [
    'heroku_hijack_collectstatic',
    'django.contrib.sites',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'health_check',
    'intake',
    'url_robots',
    'user_accounts',
    'phone',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_jinja',
    'invitations',
    'storages',
    'formation',
    'taggit',
    'debug_toolbar',
    'django_extensions',
    'compressor',
    'behave_django',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'intake.middleware.PersistReferrerMiddleware',
    'intake.middleware.PersistSourceMiddleware',
    'intake.middleware.GetCleanIpAddressMiddleware',
    'intake.middleware.CountUniqueVisitorsMiddleware'
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'NAME': 'jinja',
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [
            os.path.join(REPO_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "extensions": DEFAULT_EXTENSIONS + [
                "compressor.contrib.jinja2ext.CompressorExtension"],
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'django.template.context_processors.request',
            ],
            "globals":{
                "content": "project.content.constants",
                "linkify": "project.jinja2.linkify",
                "current_local_time": "project.jinja2.current_local_time",
                "namify": "project.jinja2.namify",
                "url_with_ids": "project.jinja2.url_with_ids",
                "oxford_comma": "project.jinja2.oxford_comma",
                "contact_info_to_html": "project.jinja2.contact_info_to_html",
                "to_json": "project.jinja2.to_json",
                "humanize": "project.jinja2.humanize",
                "contact_method_verbs": "project.jinja2.contact_method_verbs",
                "format_phone_number": "project.jinja2.format_phone_number",
                "settings": "django.conf.settings",
                "local_time": "intake.utils.local_time",
            }
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(REPO_DIR, 'project', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
# django-allauth and django-invitations
ACCOUNT_FORMS = {
    'login': 'user_accounts.forms.LoginForm'
}
ACCOUNT_ADAPTER = 'invitations.models.InvitationsAdapter'
INVITATIONS_INVITATION_EXPIRY = 14
INVITATIONS_INVITATION_ONLY = True
INVITATIONS_SIGNUP_REDIRECT = 'account_signup'
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''  # don't prefix emails with the site name
INVITATIONS_EMAIL_SUBJECT_PREFIX = ACCOUNT_EMAIL_SUBJECT_PREFIX
# invitation only, so email confirmation is redundant
ACCOUNT_EMAIL_VERIFICATION = "none"
# they can always reset the password
ACCOUNT_SIGNUP_PASSWORD_VERIFICATION = False
ACCOUNT_EMAIL_REQUIRED = True  # ensure that people have emails
ACCOUNT_USERNAME_REQUIRED = False  # we don't need usernames
ACCOUNT_AUTHENTICATION_METHOD = "email"  # login using email
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 9
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 60
ACCOUNT_LOGOUT_ON_GET = True
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
ADMINS = [
    ('Ben', 'clearmyrecord-alerts@codeforamerica.org'),
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation'
                 '.UserAttributeSimilarityValidator'),
    }, {
        'NAME': ('django.contrib.auth.password_validation'
                 '.MinimumLengthValidator'),
    }, {
        'NAME': ('django.contrib.auth.password_validation'
                 '.CommonPasswordValidator'),
    }
]

SITE_ID = 1


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

PDFPARSER_PATH = os.path.join(REPO_DIR, 'intake', 'pdfparser.jar')

# AWS uploads
AWS_S3_FILE_OVERWRITE = False

# Static files & django-compressor settings (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_FINDERS = [
    'compressor.finders.CompressorFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


def build_precompilers(path):
    less_command = os.path.join(path, '.bin/lessc')
    exec_less = '%s --include-path=%s {infile} {outfile}' % (
        less_command,
        path,
    )
    browserify_command = os.path.join(path, '.bin/browserify')
    exec_browserify = '%s {infile} -d --outfile {outfile}' % browserify_command
    return (
        ('text/less', exec_less),
        ('text/browserify', exec_browserify)
    )


# Build Compress with Node Modules
NODE_MODULES_PATH = os.path.join(REPO_DIR, 'node_modules')
COMPRESS_PRECOMPILERS = build_precompilers(NODE_MODULES_PATH)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True


def COMPRESS_JINJA2_GET_ENVIRONMENT():
    from django.template import engines
    return engines["jinja"].env

# static files location
STATIC_ROOT = os.path.join(REPO_DIR, 'staticfiles')
