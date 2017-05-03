from project.settings.environment import *

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False

# Build Compress with Node Modules
NODE_MODULES_PATH = os.path.join(REPO_DIR, 'node_modules')
COMPRESS_PRECOMPILERS = build_precompilers(NODE_MODULES_PATH)
