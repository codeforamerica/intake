from django.test import TestCase
from django.core.urlresolvers import reverse


class TestPersistReferrerMiddleware(TestCase):

    def test_persist_external_referrer(self):
        referrer = 'http://backtothefuture.com'
        response = self.client.get(
            reverse('intake-home'),
            HTTP_REFERER=referrer
        )
        self.assertEqual(referrer, self.client.session['referrer'])

        self.client.get(
            reverse('intake-apply'),
            HTTP_REFERER=response.wsgi_request.build_absolute_uri())
        self.assertEqual(referrer, self.client.session['referrer'])

    def test_no_referrer_does_nothing(self):

        self.client.get(reverse('intake-home'))
        self.assertIsNone(self.client.session.get('referrer'))
       