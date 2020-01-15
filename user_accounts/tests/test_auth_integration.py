from unittest.mock import patch

from django.core import mail
from django.urls import reverse
from django.utils import html as html_utils
from django.contrib.auth.models import User, Group

from user_accounts.forms import InviteForm
from user_accounts.models import (
    Invitation,
    get_user_display
)

from user_accounts.tests.base_testcases import AuthIntegrationTestCase


class TestUserAccounts(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations', 'groups', 'mock_profiles']

    def test_invite_form_has_the_right_fields(self):
        form = InviteForm()
        form_html = form.as_p()
        for org in self.orgs:
            self.assertIn(
                html_utils.escape(org.name),
                form_html)
        for group in Group.objects.all():
            self.assertIn(
                html_utils.escape(group.name),
                form_html)

    def test_invite_form_saves_correctly(self):
        form = InviteForm(dict(
            email="someone@example.com",
            organization=self.orgs[0].id,
            groups=[self.groups[0].id],
            should_get_notifications=True
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

    def test_superuser_can_invite_people(self):
        self.be_superuser()
        self.client.fill_form(
            reverse(self.send_invite_view),
            email=self.example_user['email'],
            organization=self.orgs[0].id,
            groups=[self.groups[0].id],
            should_get_notifications=True,
            follow=True,
        )
        last_email = mail.outbox[-1]
        self.assertEqual(self.example_user['email'], last_email.to[0])
        self.assertIn(
            "You've been invited to create an account on Clear My Record",
            last_email.body)

    @patch('user_accounts.models.user_profile.tasks')
    def test_invited_person_can_signup(self, mock_tasks):
        self.be_superuser()
        response = self.client.fill_form(
            reverse(self.send_invite_view),
            email=self.example_user['email'],
            organization=self.orgs[0].id,
            groups=[self.groups[0].id],
            should_get_notifications=True,
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
        self.assertIn(self.example_user['email'], get_user_display(users[0]))
        self.assertIn(self.groups[0], users[0].groups.all())
        mock_tasks.create_mailgun_route.assert_called_once_with(
            users[0].profile.id)

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
        user = User.objects.first()
        expected_error_message = str(
            "Sorry, that email and password do not work together")
        response = self.client.fill_form(
            reverse(self.login_view),
            login=user.email,
            password='incorrect'
        )
        # should be storing the login email for the reset page
        session = response.wsgi_request.session
        self.assertEqual(
            session['failed_login_email'],
            user.email)
        form = response.context_data['form']
        self.assertIn(expected_error_message,
                      form.errors['__all__'])
        self.assertContains(
            response,
            reverse(self.reset_password_view)
        )

    def test_can_reset_password_from_login_page(self):
        self.be_anonymous()
        user = User.objects.first()
        # forget password
        wrong_password = self.client.fill_form(
            reverse(self.login_view),
            login=user.email,
            password='forgot'
        )
        # find a link to reset password
        self.assertContains(wrong_password,
                            reverse(self.reset_password_view))
        # hit "reset password"
        reset = self.client.get(
            reverse(self.reset_password_view))
        self.assertContains(reset, user.email)
        # enter email to request password reset
        self.client.fill_form(
            reverse(self.reset_password_view),
            email=user.email,
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
        self.assertContains(reset_page, user.email)
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
        self.assertLoggedInAs(user)
        # make sure we can login with the new password
        self.client.logout()
        self.client.login(
            email=user.email,
            password=new_password
        )
        self.assertLoggedInAs(user)

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

    def test_only_staff_users_cant_invite_people(self):
        self.be_apubdef_user()
        response = self.client.get(reverse(self.send_invite_view))
        self.assertEqual(response.status_code, 302)
        self.be_monitor_user()
        response = self.client.get(reverse(self.send_invite_view))
        self.assertEqual(response.status_code, 302)
        self.be_cfa_user()
        response = self.client.get(reverse(self.send_invite_view))
        self.assertEqual(response.status_code, 200)
