from django.test import TestCase
from project.services import logging_service
from unittest.mock import patch
from logging import INFO


class TestFormatAndLog(TestCase):

    @patch('django.utils.timezone.now')
    def test_logs_correct_string(self, now):
        now.return_value.strftime.return_value = 'faketime'
        expected_message = str(
            "INFO:project.services.logging_service:"
            "faketime\tcall_to_mixpanel\tchannel=subspace")
        with self.assertLogs(logging_service.logger, INFO) as logs:
            logging_service.format_and_log(
                'call_to_mixpanel', channel='subspace')
        self.assertEqual(logs.output, [expected_message])

    def test_doesnt_log_without_valid_name(self):
        with self.assertRaises(TypeError):
            logging_service.format_and_log()

    def test_doesnt_log_with_invalid_level(self):
        with self.assertRaises(AttributeError):
            logging_service.format_and_log('set_phasers', level='stun')
