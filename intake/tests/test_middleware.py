from unittest.mock import Mock, patch
from django.test import TestCase
from django.urls import reverse

from intake.middleware import GetCleanIpAddressMiddleware
from intake import models
from django.http import HttpResponseServerError


def respond_with(response):
    def wrapped(*args, **kwargs):
        return response('Test exception')
    return wrapped


class TestUserAgentMiddleware(TestCase):

    def test_empty_user_agent_header(self):
        # Make sure that UserAgentMiddleware can still handle an empty
        # http header
        request = self.client.get(reverse('intake-home')).wsgi_request
        self.assertEqual('Other', request.user_agent.os.family)
        self.assertEqual('Other', request.user_agent.browser.family)
        self.assertEqual('Other', request.user_agent.device.family)
        self.assertEqual(False, request.user_agent.is_bot)

    def test_expected_success(self):
        user_agent_string = str(
            'Mozilla/5.0 (Linux; Android 6.0.1; Z831 Build/MMB29M) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 '
            'Mobile Safari/537.36')
        request = self.client.get(
            reverse('intake-home'), HTTP_USER_AGENT=user_agent_string
        ).wsgi_request
        self.assertEqual('Android', request.user_agent.os.family)
        self.assertEqual('Chrome Mobile', request.user_agent.browser.family)
        self.assertEqual('Z831', request.user_agent.device.family)
        self.assertEqual(False, request.user_agent.is_bot)
        self.assertEqual(True, request.user_agent.is_mobile)
        self.assertEqual(False, request.user_agent.is_tablet)


class TestPersistReferrerMiddleware(TestCase):

    def test_persist_external_referrer(self):
        referrer = 'http://backtothefuture.com'
        response = self.client.get(
            reverse('intake-home'), HTTP_REFERER=referrer)
        self.assertEqual(referrer, self.client.session['referrer'])

        self.client.get(
            reverse('intake-apply'),
            HTTP_REFERER=response.wsgi_request.build_absolute_uri())
        self.assertEqual(referrer, self.client.session['referrer'])

    def test_no_referrer_does_nothing(self):
        self.client.get(reverse('intake-home'))
        self.assertIsNone(self.client.session.get('referrer'))

    def test_ignores_health_checks(self):
        self.client.get(
            reverse('health_check-ok'),
            **{'HTTP_REFERER': 'https://wonderful.horse'})
        self.assertIsNone(self.client.session.get('referrer'))


class TestPersistSourceMiddleware(TestCase):

    def test_records_source_if_sent_as_query_param(self):
        url = reverse('intake-home')
        url += '?source=test'
        response = self.client.get(url)
        source = response.wsgi_request.session.get('source')
        self.assertEqual(source, 'test')

    def test_source_persists_between_requests(self):
        url = reverse('intake-home')
        url += '?source=test'
        self.client.get(url)
        response_2 = self.client.get(reverse('intake-apply'))
        source = response_2.wsgi_request.session.get('source')
        self.assertEqual(source, 'test')

    def test_records_nothing_if_no_source(self):
        response = self.client.get(reverse('intake-home'))
        source = response.wsgi_request.session.get('source')
        self.assertIsNone(source)

    def test_ignores_health_checks(self):
        self.client.get(reverse('health_check-ok'), {'source': 'odo'})
        self.assertIsNone(self.client.session.get('source'))


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

    def test_ignores_health_checks(self):
        response = self.client.get(
            reverse('health_check-ok'),
            **{'HTTP_X_FORWARDED_FOR': 'https://wonderful.horse'})
        self.assertFalse(hasattr(response.wsgi_request, 'ip_address'))


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
        Visitor.assert_called_once_with(
            ip_address='127.0.0.1', referrer='', source='', user_agent='',
            locale='en')

    @patch('intake.middleware.Visitor')
    def test_ignores_health_checks(self, Visitor):
        Visitor.return_value = Mock(id=1)
        response = self.client.get(reverse('health_check-ok'))
        self.assertIsNone(response.wsgi_request.session.get('visitor_id'))
        Visitor.assert_not_called()

    def test_response_view_identified(self):
        response = self.client.get(reverse('intake-apply'))
        self.assertEqual(response.view.__class__.__name__, 'SelectCountyView')

    @patch('intake.middleware.EventsService.page_viewed')
    def test_404_does_not_fire_page_viewed(self, page_viewed):
        self.client.get('/doesnotexist')
        page_viewed.assert_not_called()

    @patch('intake.middleware.EventsService.page_viewed')
    def test_redirecting_response_does_not_fire_page_viewed(self, page_viewed):
        response = self.client.get(reverse('intake-app_index'))
        page_viewed.assert_not_called()
        self.client.get(response.url)
        self.assertEqual(1, page_viewed.call_count)

    @patch('intake.middleware.EventsService.page_viewed')
    @patch('intake.views.public_views.Home.get', respond_with(
        HttpResponseServerError))
    def test_500_does_not_fire_page_viewed(self, page_viewed):
        self.client.get(reverse('intake-home'))
        page_viewed.assert_not_called()
