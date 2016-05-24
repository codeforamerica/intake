from unittest import skipIf
from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse

from tests.clients import CsrfClient

from user_accounts.models import Organization

class TestAuth(TestCase):

    client_class = CsrfClient

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

    superuser = dict(
            username="super",
            email="super@codeforamerica.org",
            password="en9op4gI4jil0"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # make a super user
        from django.contrib.auth.models import User
        User.objects.create_superuser(**cls.superuser)

    def have_some_orgs(self):
        if not getattr(self, 'orgs', None):
            self.orgs = [
                Organization(name=n)
                for n in ["Org A", "Org B"]
                ]
            for org in self.orgs:
                org.save()

    def fill_form(self, url, **data):
        follow = data.pop('follow', False)
        response = self.client.get(url)
        # if csrf protected, get the token
        csrf_token = None
        if self.__class__.client_class == CsrfClient:
            csrf_token = response.cookies['csrftoken'].value
        data.update(csrfmiddlewaretoken=csrf_token)
        return self.client.post(url, data, follow=follow)

    def follow_redirect(self, response):
        return self.client.get(response.url)

    def be_superuser(self):
        self.client.login(**self.superuser)

    def be_staff_user(self):
        pass

    def test_uninvited_signups_are_redirected_to_home(self):
        # be anonymous
        self.client.logout()
        # try to go to signup page
        response = self.client.get(
            reverse(self.signup_view)
            )
        # get redirected to splash page
        self.assertRedirects(response, reverse('intake-home'))

    def test_superuser_can_add_organization(self):
        self.be_superuser()
        # add an organization
        response = self.fill_form(
            reverse('admin:user_accounts_organization_add'),
            name='East Bay Community Law Center'
            )
        self.assertRedirects(response,
            reverse('admin:user_accounts_organization_changelist'))
        result = self.follow_redirect(response)
        self.assertContains(result, 'East Bay Community Law Center')

    def test_superuser_can_invite_people(self):
        self.be_superuser()
        self.have_some_orgs()
        response = self.fill_form(
            reverse(self.send_invite_view),
            email="Andrew.Strawberry@legalaid.org",
            organization=self.orgs[0].id,
            follow=True,
            )
        last_email = mail.outbox[-1]
        self.assertEqual("Andrew.Strawberry@legalaid.org", last_email.to[0])
        self.assertIn("invited to join", last_email.body)

    @skipIf(True, "not yet implemented")
    def test_invited_person_can_signup(self):
        # get an email invite
        # click on link
        # enter password, hit enter
        # be staff user
        pass

    @skipIf(True, "not yet implemented")
    def test_user_can_add_info(self):
        # be logged in staff user
        # find link to profile
        # edit name
        pass

    @skipIf(True, "not yet implemented")
    def test_user_can_reset_password(self):
        # be logged in user
        # find link to profile
        # click to reset password
        # enter new password, hit return
        # get confirmation
        # logout
        # login with new password
        pass

    @skipIf(True, "not yet implemented")
    def test_failed_login_gets_error_message(self):
        # be anonymous
        # go to login page
        # enter wrong password
        # be able to understand error message
        pass

    @skipIf(True, "not yet implemented")
    def test_can_reset_password_from_login_page(self):
        # be anonymous
        # go to login page
        # hit "reset password"
        # enter email
        # get a confirmation that email was sent
        # get an email
        # follow link in email
        # reset password
        pass

