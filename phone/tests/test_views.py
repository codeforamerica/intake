from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.core import mail


class TestHandleIncomingCallView(TestCase):
    expected_twiml_fragments = [
        str(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Response>'
            '<Play>/static/voicemail/CMR_voicemail_greeting.mp3</Play>'
            '<Record '
            'action="https://'), str('phone/handle-new-message" '
                                     'method="POST" />'
                                     '</Response>')]

    def test_get(self):
        response = self.client.get(reverse('phone-handle_incoming_call'))
        # should return 405 NOT ALLOWED
        self.assertEqual(response.status_code, 405)

    @patch('phone.views.static')
    @patch('phone.views.is_valid_twilio_request')
    def test_successful_post(self, is_valid, static):
        static.return_value = '/static/voicemail/CMR_voicemail_greeting.mp3'
        is_valid.return_value = True
        response = self.client.post(reverse('phone-handle_incoming_call'), {})
        self.assertEqual(response.status_code, 200)
        for fragment in self.expected_twiml_fragments:
            self.assertContains(response, fragment)
        is_valid.assert_called_once_with(response.wsgi_request)

    @patch('phone.views.is_valid_twilio_request')
    def test_invalid_post(self, is_valid):
        is_valid.return_value = False
        response = self.client.post(reverse('phone-handle_incoming_call'), {})
        self.assertEqual(response.status_code, 404)
        is_valid.assert_called_once_with(response.wsgi_request)


class TestHandleVoicemailRecordingView(TestCase):
    expected_email_subject = 'New voicemail TIME'
    expected_email_body = '''New voicemail from +15555555

Received: TIME

Listen to the recording at
    https://api.twilio.com/something/something'''
    post_data = {
        'RecordingUrl': 'https://api.twilio.com/something/something',
        'From': '+15555555',
    }

    @patch('phone.views.is_valid_twilio_request')
    @patch('phone.views.get_time_received')
    def test_successful_post(self, get_time_received, is_valid):
        get_time_received.return_value = 'TIME'
        is_valid.return_value = True
        response = self.client.post(
            reverse('phone-handle_new_message'), self.post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.content)
        is_valid.assert_called_once_with(response.wsgi_request)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, self.expected_email_subject)
        self.assertEqual(email.body, self.expected_email_body)

    @patch('phone.views.is_valid_twilio_request')
    def test_invalid_post(self, is_valid):
        is_valid.return_value = False
        response = self.client.post(
            reverse('phone-handle_new_message'), self.post_data)
        self.assertEqual(response.status_code, 404)
        is_valid.assert_called_once_with(response.wsgi_request)

    def test_get(self):
        response = self.client.get(reverse('phone-handle_new_message'))
        # should return 405 NOT ALLOWED
        self.assertEqual(response.status_code, 405)
