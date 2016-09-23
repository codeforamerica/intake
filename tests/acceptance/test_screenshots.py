import re
import random

from django.test import override_settings
from django.core import mail
from django.core.urlresolvers import reverse

from intake import models, constants
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

    fixtures = ['counties', 'organizations', 'mock_profiles']

    def setUp(self):
        super().setUp()
        orgs = accounts_models.Organization.objects.all()
        for org in orgs:
            setattr(self, org.slug, org)
            setattr(self, org.slug+'_submissions', [])
            user = auth_models.User.objects.filter(
                profile__organization=org, email__contains='+').first()
            setattr(self, org.slug+'_user', user)
        org_sets = [
            [self.sf_pubdef],
            [self.sf_pubdef],
            [self.sf_pubdef],
            [self.sf_pubdef, self.cc_pubdef],
            [self.cc_pubdef],
            [self.cc_pubdef],
            [self.a_pubdef],
            [self.a_pubdef],
            [self.a_pubdef, self.cc_pubdef],
            [self.a_pubdef, self.sf_pubdef],
            [self.a_pubdef, self.sf_pubdef, self.cc_pubdef],
        ]
        counties = models.County.objects.all()
        for county in counties:
            if county.slug == constants.Counties.SAN_FRANCISCO:
                self.sfcounty = county
            elif county.slug == constants.Counties.CONTRA_COSTA:
                self.cccounty = county
        self.submissions = []
        for org_set in org_sets:
            answers = {
                **intake_mock.fake.cleaned_sf_county_form_answers(),
                **intake_mock.fake.contra_costa_county_form_answers(),
                **intake_mock.fake.alameda_county_form_answers(),
                **intake_mock.fake.declaration_letter_answers(),
            }
            sub = models.FormSubmission.create_for_organizations(
                    organizations=org_set, answers=answers)
            self.submissions.append(sub)
            for org in org_set:
                if org.slug != 'cfa':
                    attr_name = org.slug+'_submissions'
                    org_subs = getattr(self, attr_name)
                    org_subs.append(sub)
                    setattr(self, attr_name, org_subs)
        self.pdf = intake_mock.useable_pdf(self.sf_pubdef)
        self.superuser = auth_mock.fake_superuser()
        accounts_models.UserProfile.objects.create(
            user=self.superuser,
            organization=self.cfa)

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
                S.get("partners", '/partners/'),
                S.get("EBCLC partner page", '/partners/ebclc/'),
                S.get("SF partner page", '/partners/sf_pubdef/'),
            ],
            size=base.SMALL_DESKTOP
        )

    def test_apply_to_san_francisco(self):
        answers = intake_mock.fake.sf_county_form_answers()
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('selected San Francisco', counties=['sanfrancisco']),
            S.fill_form('submitted form', **answers)
        ]
        sizes = {
            'Apply on a common mobile phone': base.COMMON_MOBILE,
            'Apply on a small desktop computer': base.SMALL_DESKTOP
        }
        for prefix, size in sizes.items():
            self.run_sequence(prefix, sequence, size=size)

    def test_application_submission_failure(self):
        address_fields = {
            key: value
            for key, value in intake_mock.fake.sf_county_form_answers().items()
            if 'address' in key
        }
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('selected San Francisco', counties=['sanfrancisco']),
            S.fill_form('submitted incomplete form', first_name='Cornelius'),
            S.fill_form('added last name', last_name='Cherimoya'),
            S.fill_form('added address', contact_preferences=[
                        'prefers_snailmail'], **address_fields)
        ]
        self.run_sequence(
            "Applying without enough information",
            sequence,
            size=base.COMMON_MOBILE)

    def test_login_and_password_reset_workflow(self):
        user = self.cc_pubdef_user
        self.run_sequence(
            "Fail login and reset password",
            [
                S.get('went to login', reverse(AuthCase.login_view)),
                S.fill_form(
                    'entered login info',
                    login=user.email,
                    password="incorrect"),
                S.click_on('clicked forgot password', "Forgot Password?"),
                S.fill_form('entered email', email=user.email),
                S.check_email('reset email'),
                S.get('clicked on link in email', self.get_link_from_email),
                S.fill_form('entered new password', password=fake_password),
            ], base.SMALL_DESKTOP)

    def test_invite_user_workflow(self):
        superuser = self.cfa_user
        organization = self.sf_pubdef
        new_user = auth_mock.fake_user_data()
        self.run_sequence(
            "Invitation and signup",
            [
                S.get('went to login', reverse(AuthCase.login_view)),
                S.fill_form(
                    'entered login info',
                    login=superuser.email,
                    password=fake_password),
                S.get(
                    'went to send invite view', reverse(
                        AuthCase.send_invite_view)),
                S.fill_form(
                    'submitted email and an org',
                    email=new_user['email'],
                    organization=str(
                        organization.id)),
                S.get('logged out', reverse(AuthCase.logout_view)),
                S.check_email('invite email'),
                S.get('clicked link in email', self.get_link_from_email),
                S.fill_form(
                    'entered name and password',
                    name='Bartholomew McHumanperson',
                    password1=fake_password),
                S.get('went to applications', reverse('intake-app_index')),
            ], base.SMALL_DESKTOP)

    def test_look_at_app_detail_with_pdf(self):
        user = self.sf_pubdef_user
        submission = random.choice(self.sf_pubdef_submissions)
        self.run_sequence(
            "Look at app with pdf",
            [
                S.get('tried to go to app detail',
                      reverse('intake-app_detail',
                              kwargs={'submission_id': submission.id})),
                S.fill_form('entered login info',
                            login=user.email, password=fake_password),
                S.wait('wait for pdf to load', 1)
            ], base.SMALL_DESKTOP)

    def test_look_at_app_detail_without_pdf(self):
        user = self.cc_pubdef_user
        submission = random.choice(self.cc_pubdef_submissions)
        self.run_sequence(
            "Look at app detail",
            [
                S.get('tried to go to app detail',
                      reverse('intake-app_detail',
                              kwargs={'submission_id': submission.id})),
                S.fill_form('entered login info',
                            login=user.email, password=fake_password)
            ], base.SMALL_DESKTOP)

    def test_look_at_alameda_app_detail(self):
        user = self.a_pubdef_user
        submission = random.choice(self.a_pubdef_submissions)
        self.run_sequence(
            "Look at alameda app detail",
            [
                S.get('tried to go to app detail',
                      reverse('intake-app_detail',
                              kwargs={'submission_id': submission.id})),
                S.fill_form('entered login info',
                            login=user.email, password=fake_password)
            ], base.SMALL_DESKTOP)

    def test_look_at_app_bundle_with_pdf(self):
        user = self.sf_pubdef_user
        bundle = models.ApplicationBundle.create_with_submissions(
            submissions=self.sf_pubdef_submissions,
            organization=self.sf_pubdef)
        self.run_sequence(
            "Look at app pdf bundle",
            [
                S.get('tried to go to app bundle',
                      reverse('intake-app_bundle_detail',
                              kwargs=dict(bundle_id=bundle.id))),
                S.fill_form('entered login info',
                            login=user.email, password=fake_password),
                S.wait('wait for pdf to load', 2)
            ], base.SMALL_DESKTOP)

    def test_look_at_app_bundle_without_pdf(self):
        user = self.cc_pubdef_user
        bundle = models.ApplicationBundle.create_with_submissions(
            submissions=self.cc_pubdef_submissions,
            organization=self.cc_pubdef)
        self.run_sequence(
            "Look at app bundle",
            [
                S.get('tried to go to app bundle',
                      reverse('intake-app_bundle_detail',
                              kwargs=dict(bundle_id=bundle.id))),
                S.fill_form('entered login info',
                            login=user.email, password=fake_password)
            ], base.SMALL_DESKTOP)

    def test_apply_to_contra_costa(self):
        answers = intake_mock.fake.contra_costa_county_form_answers()
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('picked contra costa', counties=['contracosta']),
            S.fill_form('submitted form', **answers),
        ]
        self.run_sequence(
            'Apply to Contra Costa',
            sequence,
            size=base.COMMON_MOBILE)

    def test_apply_to_alameda_pubdef(self):
        answers = intake_mock.fake.alameda_pubdef_answers()
        declaration_letter_answers = \
            intake_mock.fake.declaration_letter_answers()
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('picked alameda', counties=['alameda']),
            S.fill_form('submitted form', **answers),
            S.fill_form(
                'submitted declaration letter', **declaration_letter_answers),
            S.fill_form(
                'approved declaration letter', submit_action='approve_letter'),
        ]
        self.run_sequence(
            'Apply to Alameda Public Defender',
            sequence,
            size=base.COMMON_MOBILE)

    def test_apply_to_ebclc(self):
        answers = intake_mock.fake.ebclc_answers()
        sequence = [
            S.get('went to splash page', '/'),
            S.click_on('clicked apply now', 'Apply now'),
            S.fill_form('picked alameda', counties=['alameda']),
            S.fill_form('submitted form', **answers),
        ]
        self.run_sequence(
            'Apply to EBCLC in Alameda',
            sequence,
            size=base.COMMON_MOBILE)
