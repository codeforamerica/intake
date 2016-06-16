from unittest import skipIf

from django.core.urlresolvers import reverse

from tests import base
from tests import sequence_steps as S
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase as AuthCase
from user_accounts.tests.mock import create_fake_auth_models
from intake.tests import mock as intake_mock

class TestWorkflows(base.ScreenSequenceTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for key, models in create_fake_auth_models().items():
            setattr(cls, key, models)

    def test_application_submission_workflow(self):
        # self.host = 'https://clearmyrecord.codeforamerica.org'
        sequence = [
            S.get('/'),
            S.click_on('Apply now'),
            S.fill_form(**intake_mock.fake.sf_county_form_answers()),
            ]
        sizes = {
            'Apply on a common mobile phone': base.COMMON_MOBILE,
            'Apply on a small mobile phone': base.SMALL_MOBILE,
            'Apply on a small desktop computer': base.SMALL_DESKTOP
        }
        for prefix, size in sizes.items():
            self.run_sequence(prefix, sequence, size=size)

    @skipIf(True, "not yet implemented")
    def test_login_workflow(self):
        pass

    @skipIf(True, "not yet implemented")
    def test_invite_user_workflow(self):
        sequence = [
            reverse(AuthCase.send_invite_view),
        ]

    def test_app_index(self):
        self.run_sequence(
            "Go to application index",
            [S.get('/applications/')],
            base.SMALL_DESKTOP)

    @skipIf(True, "not yet implemented")
    def test_password_reset_workflow(self):
        pass

    @skipIf(True, "not yet implemented")
    def test_logout_workflow(self):
        pass