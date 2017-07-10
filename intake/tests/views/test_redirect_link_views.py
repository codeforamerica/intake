from django.core.urlresolvers import reverse
from django.test import TestCase


class TestUnreadEmailRedirectView(TestCase):
    def test_clicking_unread_link_in_email_redirects_to_unread_tab(self):
        """
        TODO: log in as a user -- test will fail bc of redirect to auth until
        this is filled in
        """
        url = reverse('intake-unread_email_redirect')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('intake-app_unread_index'))
