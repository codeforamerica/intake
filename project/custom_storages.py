from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import get_storage_class


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET


class CachedS3BotoStorage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally, too.
    """

    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        self.local_storage._save(name, content)
        super(CachedS3BotoStorage, self).save(
            name, self.local_storage._open(name))

    # HERE is secret to dont generating multiple manifest.json
    # and to delete manifest.json in Amazon S3
    def get_available_name(self, name):
        if self.exists(name):
            self.delete(name)
        return name
