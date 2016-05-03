from django.test import TestCase
from django.core.urlresolvers import reverse



class TestViews(TestCase):

    def test_home_view(self):
        response = self.client.get(reverse('intake-home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Clear My Record', response.content.decode('utf-8'))

