import re
from unittest import skipIf
from unittest.mock import Mock, patch

from django.test import override_settings
from django.core import mail
from django.core.urlresolvers import reverse

from tests import base
from tests import sequence_steps as S
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase as AuthCase
from user_accounts.tests import mock as auth_mock
from django.contrib.auth import models as auth_models
from user_accounts import models as accounts_models
from intake.tests import mock as intake_mock
fake_password = auth_mock.fake_password



@override_settings(DIVERT_REMOTE_CONNECTIONS=True)
class TestWorkflows(base.ScreenSequenceTestCase):

    def setUp(self):
        super().setUp()
        for key, models in auth_mock.create_fake_auth_models().items():
            setattr(self, key, models)
        self.submissions = intake_mock.FormSubmissionFactory.create_batch(10)
        self.superuser = auth_mock.fake_superuser()
        accounts_models.UserProfile.objects.create(
            user=self.superuser,
            organization=self.organizations[-1])

    def get_link_from_email(self):
        self.browser.delete_all_cookies()
        reset_email = mail.outbox[-1]
        # https://regex101.com/r/kP0qH7/1
        result = re.search(
            self.host + r'(?P<link>.*)',
            reset_email.body)
        self.assertTrue(result)
        return result.group('link')

    def test_public_views(self):
        self.run_sequence(
            "Browse public views",
            [
                S.get("splash page", '/'),
                S.get("application form", '/apply/'),
                S.get("thanks page", '/thanks/'),
                S.get("privacy policy", '/privacy/'),
                S.get("stats", '/stats/'),
            ],
            size=base.SMALL_DESKTOP
            )

    def test_application_submission_workflow(self):
        # self.host = 'https://cmr-dev.herokuapp.com'
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('submitted form', **intake_mock.fake.sf_county_form_answers()),
            S.click_on('clicked privacy policy', 'Privacy Policy'),
            ]
        sizes = {
            'Apply on a common mobile phone': base.COMMON_MOBILE,
            # 'Apply on a small mobile phone': base.SMALL_MOBILE,
            # 'Apply on a small desktop computer': base.SMALL_DESKTOP
        }
        for prefix, size in sizes.items():
            self.run_sequence(prefix, sequence, size=size)

    def test_application_submission_failure(self):
        address_fields = {
            key: value for key, value in intake_mock.fake.sf_county_form_answers().items()
            if 'address' in key
            }
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('submitted incomplete form', first_name='Cornelius'),
            S.fill_form('added last name', last_name='Cherimoya'),
            S.fill_form('added address', **address_fields)
        ]
        self.run_sequence(
            "Applying without enough information", sequence, size=base.COMMON_MOBILE)

    def test_login_and_password_reset_workflow(self):
        user = self.users[0]
        found_user = auth_models.User.objects.filter(email=user.email).first()
        self.run_sequence(
            "Fail login and reset password",
            [
                S.get('went to login', reverse(AuthCase.login_view)),
                S.fill_form('entered login info', login=user.email, password="incorrect"),
                S.click_on('clicked forgot password', "Forgot Password?"),
                S.fill_form('entered email', email=user.email),
                S.check_email('reset email'),
                S.get('clicked on link in email', self.get_link_from_email),
                S.fill_form('entered new password', password=fake_password),
            ], base.SMALL_DESKTOP )

    def test_invite_user_workflow(self):
        superuser = self.superuser
        organization = self.organizations[0]
        new_user = auth_mock.fake_user_data()

        self.run_sequence(
            "Invitation and signup",
            [
                S.get('went to login', reverse(AuthCase.login_view)),
                S.fill_form('entered login info', login=superuser.email, password=fake_password),
                S.get('went to send invite view', reverse(AuthCase.send_invite_view)),
                S.fill_form('submitted email and an org', email=new_user['email'], organization=str(organization.id)),
                S.get('logged out', reverse(AuthCase.logout_view)),
                S.check_email('invite email'),
                S.get('clicked link in email', self.get_link_from_email),
                S.fill_form('entered name and password', name='Bartholomew McHumanperson', password1=fake_password),
                S.get('went to applications', reverse('intake-app_index')),
            ], base.SMALL_DESKTOP )

