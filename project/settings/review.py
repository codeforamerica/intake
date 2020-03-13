import dj_database_url
from project.settings.deployed import *

# looks for 'DATABASE_URL' environmental variable
DATABASES = {
    'default': dj_database_url.config(ssl_require=True),
    'purged': dj_database_url.config(ssl_require=True),
}

# Settings for file uploads
AWS_ACCESS_KEY_ID = os.environ.get('BUCKETEER_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('BUCKETEER_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('BUCKETEER_BUCKET_NAME')
