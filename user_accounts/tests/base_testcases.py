import re
from django.test import TestCase
from django.contrib import auth
from user_accounts.tests import clients, mock
from user_accounts.models import Organization, UserProfile


class AuthIntegrationTestCase(TestCase):
    """
    A class for integration tests that depend on
    authentication and user accounts
    """

    client_class = clients.CsrfClient
    signup_view = 'account_signup'
    login_view = 'account_login'
    logout_view = 'account_logout'
    reset_password_view = 'account_reset_password'
    reset_password_done_view = 'account_reset_password_done'
    reset_password_from_key_view = 'account_reset_password_from_key'
    reset_password_from_key_done_view = 'account_reset_password_from_key_done'
    change_password_view = 'account_change_password'
    set_password_view = 'account_set_password'
    email_verification_sent_view = 'account_email_verification_sent'
    confirm_email_view = 'account_confirm_email'
    send_invite_view = 'invitations:send-invite'

    example_superuser = dict(
        username="super",
        email="super@codeforamerica.org",
        password=mock.fake_password
    )

    example_user = dict(
        email="Andrew.Strawberry@legalaid.org",
        password="5up3r S3cr3tZ!",
        name="Andrew Strawberry"
    )

    @classmethod
    def setUpTestData(cls):
        cls.orgs = Organization.objects.all()
        profiles = UserProfile.objects.all()
        cls.groups = list(auth.models.Group.objects.all())
        # set orgs by slug
        for org in cls.orgs:
            setattr(cls, org.slug, org)
        if profiles:
            for org in cls.orgs:
                user_att = org.slug + "_user"
                profile = org.profiles.first()
                if profile:
                    setattr(cls, user_att, profile.user)
        cls.superuser = mock.fake_superuser(
            **cls.example_superuser)
        UserProfile.objects.create(user=cls.superuser,
                                   organization=cls.cfa)
        cls.monitor_user = auth.models.User.objects.filter(
            username='monitor_user').first()

    def set_session(self, **data):
        session = self.client.session
        for key, value in data.items():
            session[key] = value
        session.save()

    def set_querydictifiable_session(self, **data):
        for session_key, dict_like_object in data.items():
            querydictifiable_data = {}
            for key, value in dict_like_object.items():
                if not isinstance(value, list):
                    value = [value]
                querydictifiable_data[key] = value
            self.set_session(**{session_key: querydictifiable_data})

    def be_superuser(self):
        self.client.login(**self.example_superuser)

    def be_user(self, user):
        self.client.login(
            email=user.email,
            password=mock.fake_password)
        return user

    def be_sfpubdef_user(self):
        return self.be_user(self.sf_pubdef_user)

    def be_ccpubdef_user(self):
        return self.be_user(self.cc_pubdef_user)

    def be_apubdef_user(self):
        return self.be_user(self.a_pubdef_user)

    def be_cfa_user(self):
        return self.be_user(self.cfa_user)

    def be_monitor_user(self):
        return self.be_user(self.monitor_user)

    def be_anonymous(self):
        self.client.logout()

    def assertLoggedInAs(self, user):
        client_user = auth.get_user(self.client)
        self.assertEqual(client_user, user)
        assert client_user.is_authenticated()

    def get_link_from_email(self, email):
        # https://regex101.com/r/kP0qH7/1
        link = re.search(
            r'http://testserver(?P<link>.*)',
            email.body).group('link')
        self.assertTrue(link)
        return link
