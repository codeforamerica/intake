from project.settings.environment import *

DEBUG = True

INTERNAL_IPS = ['127.0.0.1', '::1']
CELERY_TASK_ALWAYS_EAGER = True

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.core.files.storage.FileSystemStorage'

MEDIA_ROOT = os.path.join(REPO_DIR, 'project', 'media')

BROWSER_STACK_ID = os.environ.get('BROWSER_STACK_ID')
BROWSER_STACK_KEY = os.environ.get('BROWSER_STACK_KEY')

COMPRESS_OFFLINE = False
