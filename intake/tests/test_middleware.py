from unittest.mock import Mock, patch
from django.test import TestCase
from django.core.urlresolvers import reverse

from intake.middleware import GetCleanIpAddressMiddleware
from intake import models


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


class TestGetCleanIpAddressMiddleware(TestCase):

    def test_attribute_is_populated_on_ip(self):
        response = self.client.get(reverse('intake-home'))
        self.assertTrue(response.wsgi_request.ip_address)

    def test_gets_x_forwarded_for_if_multiple(self):
        mock_request = Mock()
        mock_request.META = {
            'HTTP_X_FORWARDED_FOR': 'fake_ip1,fake_ip2',
            'REMOTE_ADDR': 'no',
        }
        middleware = GetCleanIpAddressMiddleware()
        result = middleware._get_client_ip(mock_request)
        self.assertEqual(result, 'fake_ip1')

    def test_gets_single_x_forwarded_for(self):
        mock_request = Mock()
        mock_request.META = {'HTTP_X_FORWARDED_FOR': 'fake_ip1'}
        middleware = GetCleanIpAddressMiddleware()
        result = middleware._get_client_ip(mock_request)
        self.assertEqual(result, 'fake_ip1')

    def test_gets_remote_addr(self):
        mock_request = Mock()
        mock_request.META = {'REMOTE_ADDR': 'fake_ip1'}
        middleware = GetCleanIpAddressMiddleware()
        result = middleware._get_client_ip(mock_request)
        self.assertEqual(result, 'fake_ip1')


class TestCountUniqueVisitorsMiddleware(TestCase):

    def test_new_visitor_is_created_on_pageview(self):
        response = self.client.get(reverse('intake-home'))
        visitor_id = response.wsgi_request.session.get('visitor_id')
        self.assertTrue(visitor_id)
        visitor = models.Visitor.objects.get(pk=visitor_id)
        self.assertTrue(visitor)

    @patch('intake.middleware.Visitor')
    def test_visitor_is_created_only_once(self, Visitor):
        Visitor.return_value = Mock(id=1)
        response = self.client.get(reverse('intake-home'))
        visitor_id = response.wsgi_request.session.get('visitor_id')
        response_2 = self.client.get(reverse('intake-apply'))
        visitor_id_2 = response_2.wsgi_request.session.get('visitor_id')
        self.assertEqual(visitor_id, visitor_id_2)
        Visitor.assert_called_once_with(referrer='', source='')
