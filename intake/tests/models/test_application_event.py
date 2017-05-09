from unittest.mock import patch
from django.test import TestCase

from intake import models
from intake.tests import factories


class TestApplicationEvent(TestCase):

    @patch('intake.models.application_event.log_to_mixpanel')
    def test_that_pii_and_sensitive_info_is_not_sent_to_mixpanel(
            self, mixpanel):
        sub = factories.FormSubmissionFactory.create()
        for log_call in ('log_followup_sent', 'log_confirmation_sent'):
            getattr(models.ApplicationEvent, log_call)(
                sub.applicant_id,
                sub,
                contact_info=dict(
                    sms='5555555555',
                    email='someone@nowhere.horse'),
                message_content=dict(
                    subject='*^ d34thsT4R 5ch3M4tikz --*$#',
                    body=str("                        "
                             "      .#########.       "
                             "    ###############     "
                             "   #####------######    "
                             "   ###/.........\####   "
                             "  ####|.........|#####  "
                             "  ####|..(*)....|#####  "
                             "   ####\......./#####   "
                             "    #####-----######    "
                             "     ########[x]###     "
                             "       .########.       "
                             "                        ")))
            mock_args, mock_kwargs = mixpanel.delay.call_args
            applicant_id, name, data = mock_args
            self.assertEqual(type(data['contact_info']), list)
            self.assertNotIn('message_content', data)
