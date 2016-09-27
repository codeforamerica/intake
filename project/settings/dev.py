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
