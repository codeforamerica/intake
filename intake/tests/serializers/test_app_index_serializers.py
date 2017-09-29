from django.test import TestCase
from intake import models, serializers
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES


class TestApplicationIndexSerializer(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_has_correct_keys(self):
        application = models.Application.objects.first()
        data = serializers.ApplicationIndexSerializer(application).data
        self.assertIn('form_submission', data)
        self.assertNotIn('organization', data)
        self.assertIn('latest_status', data)
        self.assertIn('status_updates', data)
        self.assertIn('was_transferred_out', data)


class TestApplicationIndexWithTransfersSerializer(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_has_correct_keys(self):
        application = models.Application.objects.first()
        data = serializers.ApplicationIndexWithTransfersSerializer(
            application).data
        self.assertIn('form_submission', data)
        self.assertNotIn('organization', data)
        self.assertIn('latest_status', data)
        self.assertIn('status_updates', data)
        self.assertIn('was_transferred_out', data)
        self.assertIn('incoming_transfers', data)
