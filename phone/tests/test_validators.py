from unittest.mock import Mock, patch
from django.test import TestCase
from phone.validators import is_valid_twilio_request


class TestIsValidTwilioRequest(TestCase):

    @patch('phone.validators.RequestValidator')
    def test_expected_call(self, twilio_validator):
        mock_request = Mock(
            POST='some_data',
            META={'HTTP_X_TWILIO_SIGNATURE': 'signed'})
        mock_request.build_absolute_uri.return_value = 'http://something.biz/'
        with self.settings(TWILIO_AUTH_TOKEN='token'):
            is_valid_twilio_request(mock_request)
        twilio_validator.assert_called_once_with('token')
        twilio_validator.return_value.validate.assert_called_once_with(
            'https://something.biz', 'some_data', 'signed')
