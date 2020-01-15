from django.test import TestCase
from django.urls import reverse
from user_accounts.tests.mock import fake_superuser, fake_password


class TestURLPatterns(TestCase):

    def test_ok(self):
        response = self.client.get(reverse('health_check-ok'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everything seems fine")

    def test_error(self):
        su = fake_superuser()
        self.client.login(username=su.username, password=fake_password)
        with self.assertRaises(Exception) as context:
            response = self.client.get(reverse('health_check-error'))
            self.assertTrue('This is a Test' in context.exception)
