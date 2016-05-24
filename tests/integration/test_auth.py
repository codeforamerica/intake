from unittest import skipIf
from django.test import TestCase
from django.core.urlresolvers import reverse

from tests.clients import CsrfClient


class TestAuthFlows(TestCase):

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

    superuser = dict(
            username="super",
            email="super@codeforamerica.org",
            password="en9op4gI4jil0"
        )

    @classmethod
    def setUpClass(cls):
        super(TestAuthFlows, cls).setUpClass()
        # make a super user
        from django.contrib.auth.models import User
        User.objects.create_superuser(**cls.superuser)


    def fill_form(self, url, **data):
        response = self.client.get(url)
        # if csrf protected, get the token
        csrf_token = None
        if self.__class__.client_class == CsrfClient:
            csrf_token = response.cookies['csrftoken'].value
        data.update(csrfmiddlewaretoken=csrf_token)
        return self.client.post(url, data)

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


    @skipIf(True, "not yet implemented")
    def test_superuser_can_invite_people(self):
        # https://github.com/bee-keeper/django-invitations
        # be a superuser
        # go to a page
        # enter an email address and select an organization
        # get a confirmation that email was sent
        # make sure email is sent
        pass

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

