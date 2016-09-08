import re
from unittest import skipIf
from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import html as html_utils
from django.contrib import auth
from django.contrib.auth.models import User

from user_accounts.forms import InviteForm
from user_accounts.models import (
    Organization, Invitation, UserProfile,
    get_user_display
)

from user_accounts.tests import mock, clients


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
        for org in cls.orgs:
            if org.name == "San Francisco Public Defender":
                cls.sfpubdef = org
            elif org.name == "Contra Costa Public Defender":
                cls.ccpubdef = org
            elif org.name == "Code for America":
                cls.cfa = org
            elif org.name == "Alameda Public Defender":
                cls.apubdef = org
        cls.superuser = mock.fake_superuser(
            **cls.example_superuser)
        UserProfile.objects.create(user=cls.superuser,
                                   organization=cls.cfa)
        cls.invitations = []
        for org in cls.orgs:
            for i in range(2):  # 2 per org
                cls.invitations.append(
                    mock.fake_invitation(org, inviter=cls.superuser))
        cls.users = []
        for invite in cls.invitations:
            user = invite.create_user_from_invite(
                password=mock.fake_password,
                name=mock.fake.name())
            cls.users.append(user)
        cls.cfa_user = cls.cfa.profiles.first().user
        cls.sfpubdef_user = cls.sfpubdef.profiles.first().user
        cls.ccpubdef_user = cls.ccpubdef.profiles.first().user
        cls.apubdef_user = cls.apubdef.profiles.first().user

    def be_superuser(self):
        self.client.login(**self.example_superuser)

    def be_user(self, user):
        self.client.login(
            email=user.email,
            password=mock.fake_password)
        return user

    def be_sfpubdef_user(self):
        return self.be_user(self.sfpubdef_user)

    def be_ccpubdef_user(self):
        return self.be_user(self.ccpubdef_user)

    def be_apubdef_user(self):
        return self.be_user(self.apubdef_user)

    def be_cfa_user(self):
        return self.be_user(self.cfa_user)

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


class TestUserAccounts(AuthIntegrationTestCase):

    def test_invite_form_has_the_right_fields(self):
        form = InviteForm()
        email_field = form.fields['email']
        org_field = form.fields['organization']
        form_html = form.as_p()
        for org in self.orgs:
            self.assertIn(
                html_utils.escape(org.name),
                form_html)

    def test_invite_form_saves_correctly(self):
        form = InviteForm(dict(
            email="someone@example.com",
            organization=self.orgs[0].id
        ))
        self.assertTrue(form.is_valid())
        invite = form.save()
        qset = Invitation.objects.filter(
            email="someone@example.com",
            organization=self.orgs[0]
        )
        self.assertEqual(qset.first(), invite)

    def test_uninvited_signups_are_redirected_to_home(self):
        self.be_anonymous()
        # try to go to signup page
        response = self.client.get(
            reverse(self.signup_view)
        )
        # get redirected to splash page
        self.assertRedirects(response, reverse('intake-home'))

    def test_superuser_can_add_organization(self):
        self.be_superuser()
        # add an organization
        response = self.client.fill_form(
            reverse('admin:user_accounts_organization_add'),
            name='Magical Lawyers Guild',
            slug="mlg",
        )
        self.assertRedirects(response,
                             reverse('admin:user_accounts_organization_changelist'))
        result = self.client.get(response.url)
        self.assertContains(result, 'Magical Lawyers Guild')

    def test_superuser_can_invite_people(self):
        self.be_superuser()
        response = self.client.fill_form(
            reverse(self.send_invite_view),
            email=self.example_user['email'],
            organization=self.orgs[0].id,
            follow=True,
        )
        last_email = mail.outbox[-1]
        self.assertEqual(self.example_user['email'], last_email.to[0])
        self.assertIn(
            "You've been invited to create an account on Clear My Record",
            last_email.body)

    def test_invited_person_can_signup(self):
        self.be_superuser()
        response = self.client.fill_form(
            reverse(self.send_invite_view),
            email=self.example_user['email'],
            organization=self.orgs[0].id,
            follow=True,
        )
        # be anonymous
        self.be_anonymous()
        last_email = mail.outbox[-1]
        # click on link
        link = self.get_link_from_email(last_email)
        response = self.client.get(link)
        # should go to /accounts/signup/
        self.assertRedirects(response, reverse(self.signup_view))
        response = self.client.fill_form(response.url,
                                         email=self.example_user['email'],
                                         password1=self.example_user[
                                             'password']
                                         )
        self.assertRedirects(response, reverse("user_accounts-profile"))
        # make sure the user exists and that they are authenticated
        users = User.objects.filter(email=self.example_user['email'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_authenticated)
        self.assertEqual(
            get_user_display(
                users[0]),
            self.example_user['email'])

    def test_user_can_add_info_in_profile_view(self):
        user = self.be_sfpubdef_user()
        # find link to profile
        response = self.client.get(reverse("user_accounts-profile"))
        self.assertContains(response,
                            html_utils.escape(user.profile.name))
        result = self.client.fill_form(
            reverse("user_accounts-profile"),
            name=self.example_user['name'],
            follow=True
        )
        self.assertContains(result, self.example_user['name'])
        users = User.objects.filter(profile__name=self.example_user['name'])
        self.assertEqual(len(users), 1)

    def test_failed_login_gets_reasonable_error_message(self):
        self.be_anonymous()
        expected_error_message = "Sorry, that email and password do not work together"
        response = self.client.fill_form(
            reverse(self.login_view),
            login=self.users[0].email,
            password='incorrect'
        )
        # should be storing the login email for the reset page
        session = response.wsgi_request.session
        self.assertEqual(
            session['failed_login_email'],
            self.users[0].email)
        form = response.context['form']
        self.assertIn(expected_error_message,
                      form.errors['__all__'])
        self.assertContains(
            response,
            reverse(self.reset_password_view)
        )

    def test_can_reset_password_from_login_page(self):
        self.be_anonymous()
        # forget password
        wrong_password = self.client.fill_form(
            reverse(self.login_view),
            login=self.users[0].email,
            password='forgot'
        )
        # find a link to reset password
        self.assertContains(wrong_password,
                            reverse(self.reset_password_view))
        # hit "reset password"
        reset = self.client.get(
            reverse(self.reset_password_view))
        self.assertContains(reset, self.users[0].email)
        # enter email to request password reset
        reset_sent = self.client.fill_form(
            reverse(self.reset_password_view),
            email=self.users[0].email,
        )
        # get an email to reset password
        reset_email = mail.outbox[-1]
        self.assertEqual(
            'Password Reset for Clear My Record',
            reset_email.subject
        )
        # follow the link in the email
        reset_link = self.get_link_from_email(reset_email)
        reset_page = self.client.get(reset_link)
        # make sure it shows who it thinks we are
        self.assertContains(reset_page, self.users[0].email)
        # enter a new password
        csrf = self.client.get_csrf_token(reset_page)
        new_password = "FR35H H0T s3cr3tZ!1"
        reset_done = self.client.fill_form(
            reset_link, csrf_token=csrf,
            password=new_password)
        # we should be redirected to the profile
        self.assertRedirects(reset_done,
                             reverse("user_accounts-profile"))
        # make sure we are logged in
        self.assertLoggedInAs(self.users[0])
        # make sure we can login with the new password
        self.client.logout()
        self.client.login(
            email=self.users[0].email,
            password=new_password
        )
        self.assertLoggedInAs(self.users[0])

    def test_can_reset_password_while_logged_in(self):
        user = self.be_sfpubdef_user()
        # go to profile
        profile = self.client.get(
            reverse("user_accounts-profile"))
        # make sure there's a link to change password
        self.assertContains(profile,
                            reverse(self.change_password_view))
        change_password = self.client.get(
            reverse(self.change_password_view))
        # make sure the change password page
        # knows who we are
        self.assertContains(change_password,
                            user.email)
        # set a new password
        new_password = "FR35H H0T s3cr3tZ!1"
        reset_done = self.client.fill_form(
            reverse(self.change_password_view),
            password=new_password
        )
        self.assertRedirects(reset_done,
                             reverse("user_accounts-profile"))
        # make sure we are logged in
        self.assertLoggedInAs(user)
        # make sure we can login with the new password
        self.client.logout()
        self.client.login(
            email=user.email,
            password=new_password
        )
        self.assertLoggedInAs(user)
