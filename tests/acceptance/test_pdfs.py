import os
from django.test import TestCase


class TestPDFs(TestCase):

    def test_add_file_to_s3(self):
        # TODO: this can probably be removed
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        conn = S3Connection(access_key, secret_key)
        bucket = conn.get_bucket('cmr-demo')
        path = os.path.join('media', 'pdfs', 'sample_form.pdf')
        key = Key(bucket, path)
        local_path = 'tests/sample_pdfs/sample_form.pdf'
        key.set_contents_from_filename(local_path)
