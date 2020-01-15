from django.test import TestCase
from django.urls import reverse
from intake.serializers import RequestSerializer
from rest_framework.renderers import JSONRenderer


class TestRequestSerializer(TestCase):

    empty_agent_results = {
        'browser_family': 'Other',
        'browser_version': '',
        'compact_user_agent': 'Other / Other / Other',
        'device_brand': None,
        'device_family': 'Other',
        'device_model': None,
        'is_bot': False,
        'is_mobile': False,
        'is_pc': False,
        'is_tablet': False,
        'is_touch_capable': False,
        'os_family': 'Other',
        'os_version': ''}

    valid_agent_results = {
        'browser_family': 'Chrome Mobile',
        'browser_version': '58.0.3029',
        'compact_user_agent': 'Z831 / Android 6.0.1 / Chrome Mobile 58.0.3029',
        'device_brand': 'Generic_Android',
        'device_family': 'Z831',
        'device_model': 'Z831',
        'is_bot': False,
        'is_mobile': True,
        'is_pc': False,
        'is_tablet': False,
        'is_touch_capable': True,
        'os_family': 'Android',
        'os_version': '6.0.1'}

    json_chunks = [
        b'"browser_family": "Chrome Mobile"',
        b'"browser_version": "58.0.3029"',
        b'"os_family": "Android"',
        b'"os_version": "6.0.1"',
        b'"device_family": "Z831"',
        b'"device_brand": "Generic_Android"',
        b'"device_model": "Z831"',
        b'"is_mobile": true',
        b'"is_tablet": false',
        b'"is_touch_capable": true',
        b'"is_pc": false',
        b'"is_bot": false']

    def test_can_handle_empty_user_agent(self):
        request = self.client.get(reverse('intake-home')).wsgi_request
        data = RequestSerializer(request).data
        self.assertTrue(data)
        for key, expected_value in self.empty_agent_results.items():
            self.assertEqual(expected_value, data[key])

    def test_can_handle_valid_user_agent(self):
        user_agent_string = str(
            'Mozilla/5.0 (Linux; Android 6.0.1; Z831 Build/MMB29M) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 '
            'Mobile Safari/537.36')
        request = self.client.get(
            reverse('intake-home'), HTTP_USER_AGENT=user_agent_string
        ).wsgi_request
        data = RequestSerializer(request).data
        self.assertTrue(data)
        for key, expected_value in self.valid_agent_results.items():
            self.assertEqual(expected_value, data[key])

    def test_is_json_serializable(self):
        user_agent_string = str(
            'Mozilla/5.0 (Linux; Android 6.0.1; Z831 Build/MMB29M) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 '
            'Mobile Safari/537.36')
        request = self.client.get(
            reverse('intake-home'), HTTP_USER_AGENT=user_agent_string
        ).wsgi_request
        data = RequestSerializer(request).data
        json = JSONRenderer().render(data, renderer_context={'indent': 2})
        for chunk in self.json_chunks:
            self.assertIn(chunk, json)

    def test_detects_language_and_locale(self):
        locale_string = 'es-ni'
        request = self.client.get(
            reverse('intake-home'), HTTP_ACCEPT_LANGUAGE=locale_string
        ).wsgi_request
        data = RequestSerializer(request).data
        self.assertEqual('es-ni', data['locale'])
        self.assertEqual('Nicaraguan Spanish', data['language'])
