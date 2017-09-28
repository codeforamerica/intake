import json
from unittest.mock import patch
from django.test import TestCase as DjangoTestCase


class MockMailGunRequestMixin:
    '''Patches calls to the mailgun email validation service in order to 
        prevent external http requests.
        The patched service is used for validation of all application forms
    '''
    def run(self, result=None):
        with patch(
                'intake.services.contact_info_validation_service.'
                'validate_email_with_mailgun') as mock_mailgun_validation:
            mock_mailgun_validation.return_value = (True, None)
            super().run(result)


class TestCase(DjangoTestCase, MockMailGunRequestMixin):
    '''This is a base test case with default patches for the majority of unit
    tests
    '''
    pass
