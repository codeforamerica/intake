import re
from unittest import skipIf
from unittest.mock import Mock, patch

from django.core import mail
from django.core.urlresolvers import reverse

from tests import base
from tests import sequence_steps as S
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase as AuthCase
from user_accounts.tests import mock as auth_mock
from intake.tests import mock as intake_mock
fake_password = auth_mock.fake_password



class TestWorkflows(base.ScreenSequenceTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = auth_mock.fake_superuser()
        for key, models in auth_mock.create_fake_auth_models().items():
            setattr(cls, key, models)
        cls.submissions = intake_mock.FormSubmissionFactory.create_batch(10)

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.browser.delete_all_cookies()

    def get_link_from_email(self):
        reset_email = mail.outbox[-1]
        # https://regex101.com/r/kP0qH7/1
        result = re.search(
            self.host + r'(?P<link>.*)',
            reset_email.body)
        self.assertTrue(result)
        return result.group('link')

    def test_application_submission_workflow(self):
        # self.host = 'https://cmr-dev.herokuapp.com'
        sequence = [
            S.get('/'),
            S.click_on('Apply now'),
            S.fill_form(**intake_mock.fake.sf_county_form_answers()),
            ]
        sizes = {
            'Apply on a common mobile phone': base.COMMON_MOBILE,
            # 'Apply on a small mobile phone': base.SMALL_MOBILE,
            # 'Apply on a small desktop computer': base.SMALL_DESKTOP
        }
        for prefix, size in sizes.items():
            self.run_sequence(prefix, sequence, size=size)

    def test_login_and_password_reset_workflow(self):
        user = self.users[0]
        self.run_sequence(
            "Fail login and reset password",
            [
                S.get(reverse(AuthCase.login_view)),
                S.fill_form(login=user.email, password="incorrect"),
                S.click_on("Forgot Password?"),
                S.fill_form(email=user.email),
                S.check_email(),
                S.get(self.get_link_from_email),
                S.fill_form(password=fake_password),
            ], base.SMALL_DESKTOP )

    def test_invite_user_workflow(self):
        superuser = self.superuser
        new_user = auth_mock.fake_user_data()
        self.run_sequence(
            "Invitation and signup",
            [
                S.get(reverse(AuthCase.login_view)),
                S.fill_form(login=superuser.email, password=fake_password),
                S.get(reverse(AuthCase.send_invite_view)),
                S.fill_form(email=new_user['email']),
                S.check_email(),
                S.get(self.get_link_from_email),
                # S.fill_form(name="someone@agency.org", password=fake_password),
            ], base.SMALL_DESKTOP )

