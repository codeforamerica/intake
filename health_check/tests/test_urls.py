from django.test import TestCase
from django.core.urlresolvers import reverse


class TestURLPatterns(TestCase):

    def test_ok(self):
        response = self.client.get(reverse('health_check-ok'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everything seems fine")

    def test_error(self):
        response = self.client.get(reverse('health_check-error'))
        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Errors seem to work correctly", response.content.decode('utf-8'))
