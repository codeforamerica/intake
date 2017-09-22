from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import get_storage_class


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET


class CachedS3BotoStorage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally so that
    compressor can compile them.
    This currently breaks if s3 and the local directory are out of sync
    and it doesn't fix the local cache if its cleared.

    This is currently using the STATICFILES_LOCATION to fix
    an issue where its included in paths in css.

    TODO: Fix CSS and remove STATICFILES_LOCATION so that its
    at the bucket root.
    """

    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        self.local_storage._save(name, content)
        super(CachedS3BotoStorage, self).save(
            name, self.local_storage._open(name))
