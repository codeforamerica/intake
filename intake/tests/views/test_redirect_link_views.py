import logging
from django.urls import reverse
from django.test import TestCase
from django.conf import settings
from project.tests.assertions import assertInLogsCount
from user_accounts.tests.factories import fake_app_reviewer


class TestLinkRedirectEventViews(TestCase):
    fixtures = ['groups']

    url_names_and_targets = [
        ('intake-unread_email_redirect', 'intake-app_unread_index'),
        ('intake-needs_update_email_redirect',
            'intake-app_needs_update_index'),
        ('intake-all_email_redirect', 'intake-app_all_index'),
    ]

    def test_redirects_anon_to_auth(self):
        response = self.client.get(reverse('intake-unread_email_redirect'))
        self.assertRedirects(
            response, reverse('user_accounts-login') + (
                '?next=' + reverse('intake-unread_email_redirect')
                ))

    def test_redirects_authenticated_user_to_expected_url(self):
        profile = fake_app_reviewer()
        self.client.login(
            email=profile.user.email,
            password=settings.TEST_USER_PASSWORD)
        for get_url_name, target_url_name in self.url_names_and_targets:
            response = self.client.get(reverse(get_url_name))
            self.assertRedirects(response, reverse(target_url_name))

    def test_fires_event(self):
        profile = fake_app_reviewer()
        self.client.login(
            email=profile.user.email,
            password=settings.TEST_USER_PASSWORD)
        for get_url_name, target_url_name in self.url_names_and_targets:
            with self.assertLogs(
                    'project.services.logging_service', logging.INFO) as logs:
                response = self.client.get(reverse(get_url_name))
            assertInLogsCount(logs, {'event_name=user_email_link_clicked': 1})
