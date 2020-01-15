import logging
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from partnerships.models import PartnershipLead
from project.tests.assertions import assertInLogsCount


class TestHome(TestCase):

    def test_returns_200_for_anonymous(self):
        response = self.client.get(reverse('partnerships-home'))
        self.assertEqual(response.status_code, 200)


class TestContact(TestCase):

    def valid_post_data(self, **overrides):
        valid_post_data = dict(
            name='Ziggy Stardust',
            email='ziggy@mars.space',
            organization_name='Spiders from Mars',
            message='Jamming good with Weird and Gilly')
        valid_post_data.update(overrides)
        return valid_post_data

    def test_returns_200_for_anonymous(self):
        response = self.client.get(reverse('partnerships-contact'))
        self.assertEqual(response.status_code, 200)

    def test_sends_email(self):
        self.client.post(
            reverse('partnerships-contact'), self.valid_post_data())
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, 'New partnership lead from Spiders from Mars')
        expected_string = str(
            'Email: "ziggy@mars.space"\nName: "Ziggy Stardust"\n'
            'Organization: "Spiders from Mars"\n\n'
            'Jamming good with Weird and Gilly')
        self.assertIn(
            expected_string, str(email.message()))

    def test_redirects_to_partnerships_home_with_flash(self):
        response = self.client.post(
            reverse('partnerships-contact'), self.valid_post_data())
        self.assertRedirects(
            response, reverse('partnerships-home'),
            fetch_redirect_response=False)
        response = self.client.get(response.url)
        self.assertContains(
            response,
            'Thanks for reaching out! Your message has been sent')
        messages = [item for item in response.wsgi_request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('success', messages[0].tags)

    def test_can_submit_without_message(self):
        response = self.client.post(
            reverse('partnerships-contact'), self.valid_post_data(
                message=''))
        self.assertRedirects(response, reverse('partnerships-home'))

    def test_requires_fields(self):
        for field in ('name', 'email', 'organization_name'):
            response = self.client.post(
                reverse('partnerships-contact'),
                self.valid_post_data(**{field: ''}))
            self.assertEqual(
                response.status_code, 200,
                '{} should not be allowed to be empty'.format(field))
            self.assertContains(
                response,
                '<p class="text--error"><i class="icon-warning"></i>')

    def test_creates_partnership_lead(self):
        response = self.client.post(
            reverse('partnerships-contact'), self.valid_post_data())
        visitor = response.wsgi_request.visitor
        self.assertEqual(
            PartnershipLead.objects.count(), 1)
        self.assertEqual(
            PartnershipLead.objects.first().visitor, visitor)

    def test_logs_to_mixpanel(self):
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.post(
                reverse('partnerships-contact'), self.valid_post_data())
        assertInLogsCount(
            logs, {'event_name=partnership_interest_submitted': 1})
