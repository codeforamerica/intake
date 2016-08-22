import unittest
import sys


class PatchTranslationTestCase(unittest.TestCase):

    def setUp(self):
        self.add_apps_mock = unittest.mock.patch(
            'django.utils.translation.trans_real.DjangoTranslation._add_installed_apps_translations')
        self.add_apps_mock.start()

    def tearDown(self):
        self.add_apps_mock.stop()

django_only = unittest.skipUnless(
    any('manage.py' in arg for arg in sys.argv),
    'For Django test runner only')
