from project.settings.environment import *

DEBUG = True

# debug toolbar settings
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_COLLAPSED': True,
}
INTERNAL_IPS = ['127.0.0.1', '::1']

if USE_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES.insert(
        0, 'debug_toolbar.middleware.DebugToolbarMiddleware',)

CELERY_TASK_ALWAYS_EAGER = True

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = os.path.join(REPO_DIR, 'project', 'media')

BROWSER_STACK_ID = os.environ.get('BROWSER_STACK_ID')
BROWSER_STACK_KEY = os.environ.get('BROWSER_STACK_KEY')
