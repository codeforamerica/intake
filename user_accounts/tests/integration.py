import re
from unittest import skipIf
from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from user_accounts.forms import InviteForm
from user_accounts.models import (
    Organization, Invitation, UserProfile,
    get_user_display
    )

from user_accounts.tests import mock, clients


class TestUserAccounts(TestCase):

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
            password="en9op4gI4jil0"
        )

    example_user = dict(
        email="Andrew.Strawberry@legalaid.org",
        password="5up3r S3cr3tZ!",
        name="Andrew Strawberry"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.have_an_invited_user_from_each_organization()

    @classmethod
    def have_two_orgs(cls):
        organizations = getattr(cls, 'organizations', None)
        if organizations: return organizations
        cls.orgs = [
            mock.OrganizationFactory.create()
            for i in range(2)
        ]
        return cls.orgs

    @classmethod
    def have_a_superuser(cls):
        superuser = getattr(cls, 'superuser', None)
        if superuser: return superuser
        cls.superuser = mock.fake_superuser(
            **cls.example_superuser
            )
        return cls.superuser

    @classmethod
    def have_an_invite_for_each_organization(cls):
        invitations = getattr(cls, 'invitations', None)
        if invitations: return invitations
        orgs = cls.have_two_orgs()
        superuser = cls.have_a_superuser()
        cls.invitations = [
            mock.fake_invitation(org, inviter=superuser)
            for org in orgs
        ]
        return cls.invitations

    @classmethod
    def have_an_invited_user_from_each_organization(cls):
        users = getattr(cls, 'users', None)
        if users: return users
        invites = cls.have_an_invite_for_each_organization()
        cls.users = []
        for invite in invites:
            user = invite.create_user_from_invite(
                password=mock.fake_password,
                name=mock.fake.name()
                )
            cls.users.append(user)
        return cls.users

    def be_superuser(self):
        self.client.login(**self.example_superuser)

    def be_regular_user(self):
        user = self.users[0]
        self.client.login(
            email=user.email,
            password=mock.fake_password)

    def be_anonymous(self):
        self.client.logout()

    def test_invite_form_has_the_right_fields(self):
        form = InviteForm()
        email_field = form.fields['email']
        org_field = form.fields['organization']
        form_html = form.as_p()
        for org in self.orgs:
            self.assertIn(org.name, form_html)

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
            name='East Bay Community Law Center'
            )
        self.assertRedirects(response,
            reverse('admin:user_accounts_organization_changelist'))
        result = self.client.get(response.url)
        self.assertContains(result, 'East Bay Community Law Center')

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
        self.assertIn("invited to join", last_email.body)

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
        # https://regex101.com/r/kP0qH7/1
        link = re.search(
            r'http://testserver(?P<link>.*)',
            last_email.body).group('link')
        self.assertTrue(link)
        response = self.client.get(link)
        # should go to /accounts/signup/
        self.assertRedirects(response, reverse(self.signup_view))
        response = self.client.fill_form(response.url,
            email=self.example_user['email'],
            password1=self.example_user['password']
            )
        self.assertRedirects(response, reverse("user_accounts-profile"))
        # make sure the user exists and that they are authenticated
        users = User.objects.filter(email=self.example_user['email'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_authenticated)
        self.assertEqual(get_user_display(users[0]), self.example_user['email'])

    def test_user_can_add_info_in_profile_view(self):
        self.be_regular_user()
        # find link to profile
        response = self.client.get(reverse("user_accounts-profile"))
        self.assertContains(response, self.users[0].profile.name)
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
        self.assertEqual(session['login'], self.users[0].email)
        form = response.context['form']
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertIn(expected_error_message,
            form.errors['__all__'])
        # we got here
        self.assertContains(
            response,
            reverse(self.reset_password_view)
            )

    @skipIf(True, "not yet implemented")
    def test_user_can_easily_reset_password_while_logged_in(self):
        self.be_regular_user()
        response = self.client.fill_form(
            reverse(self.reset_password_view),
            email=self.users[0],
            password='incorrect',
            follow=True
            )
        import ipdb; ipdb.set_trace()
        # be logged in user
        # find link to profile
        # click to reset password
        # enter new password, hit return
        # get confirmation
        # logout
        # login with new password
        pass

    @skipIf(True, "not yet implemented")
    def test_can_reset_password_from_login_page(self):
        self.be_anonymous()
        # forget password
        response = self.client.fill_form(
            reverse(self.login_view),
            login=self.users[0].email,
            password='forgot'
            )
        # hit "reset password"
        reset = self.client.get(
            reverse(self.reset_password_view)
            )
        self.assertContains(
            reset,
            self.users[0].email
            )
        # enter email to request password reset
        reset_sent = self.client.fill_form(
            reverse(self.reset_password_view),
            email=self.users[0].email,
            )
        reset_email = mail.outbox[-1]
        import ipdb; ipdb.set_trace()
        # enter email
        # get a confirmation that email was sent
        # get an email
        # follow link in email
        # reset password
        raise Exception
