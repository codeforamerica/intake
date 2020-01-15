from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from intake.permissions import get_all_followup_permissions
from user_accounts.tests.factories import UserProfileFactory, UserFactory
from intake.tests.factories import FormSubmissionWithOrgsFactory


class SearchViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # users & subs for two orgs
        # combo sub
        # a staff user with followup permissions
        this_profile = UserProfileFactory()
        other_profile = UserProfileFactory()
        cls.org_user = this_profile.user
        cls.staff_user = UserFactory(is_staff=True)
        UserProfileFactory(user=cls.staff_user)
        cls.staff_user.user_permissions.add(*get_all_followup_permissions())
        answers = dict(
            first_name='Jorge Luis', last_name='Borges',
            email='george@fictions.book', phone_number='4152124848')
        cls.these_subs = [
            FormSubmissionWithOrgsFactory(
                organizations=[this_profile.organization],
                answers=answers) for i in (1, 2)]
        cls.other_subs = [
            FormSubmissionWithOrgsFactory(
                organizations=[other_profile.organization],
                answers=answers) for i in (1, 2)]
        cls.combo_sub = FormSubmissionWithOrgsFactory(
                organizations=[
                    this_profile.organization,
                    other_profile.organization],
                answers=answers)

    def assertContainsTheseSubs(self, response):
        for sub in self.these_subs:
            self.assertContains(response, sub.get_absolute_url())

    def assertContainsOtherSubs(self, response):
        for sub in self.other_subs:
            self.assertContains(response, sub.get_absolute_url())

    def assertNotContainsOtherSubs(self, response):
        for sub in self.other_subs:
            self.assertNotContains(response, sub.get_absolute_url())

    def assertContainsComboSub(self, response):
        self.assertContains(response, self.combo_sub.get_absolute_url())

    def login(self, user):
        self.client.login(
            username=user.username,
            password=settings.TEST_USER_PASSWORD)

    def login_as_org_user(self):
        self.login(self.org_user)

    def login_as_staff_user(self):
        self.login(self.staff_user)


class TestApplicantAutocomplete(SearchViewTestCase):
    view_name = 'applications-autocomplete'

    def test_anonymous_users_get_403(self):
        self.client.logout()
        response = self.client.post(reverse(self.view_name), {'q': 'anything'})
        self.assertEqual(response.status_code, 403)

    def test_authenticated_org_users_receive_application_jsons(self):
        self.login_as_org_user()
        response = self.client.post(reverse(self.view_name), {'q': 'Luis'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertNotContainsOtherSubs(response)

    def test_get_method_not_allowed(self):
        self.login_as_org_user()
        response = self.client.get(reverse(self.view_name), {'q': 'Luis'})
        # should return "method not allowed"
        self.assertEqual(response.status_code, 405)

    def test_staff_user_gets_200(self):
        self.login_as_staff_user()
        response = self.client.post(reverse(self.view_name), {'q': 'Luis'})
        self.assertEqual(response.status_code, 200)

    def test_can_find_app_with_phone_number(self):
        self.login_as_org_user()
        response = self.client.post(
            reverse(self.view_name), {'q': '2124848'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertNotContainsOtherSubs(response)

    def test_can_find_app_with_email(self):
        self.login_as_org_user()
        response = self.client.post(
            reverse(self.view_name), {'q': 'george@fictions'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertNotContainsOtherSubs(response)


class TestFollowupsAutocomplete(SearchViewTestCase):
    view_name = 'followups-autocomplete'

    def test_anonymous_users_get_403(self):
        self.client.logout()
        response = self.client.post(reverse(self.view_name), {'q': 'Luis'})
        self.assertEqual(response.status_code, 403)

    def test_org_users_get_403(self):
        self.login_as_org_user()
        response = self.client.post(reverse(self.view_name), {'q': 'Luis'})
        self.assertEqual(response.status_code, 403)

    def test_staff_users_receive_html(self):
        self.login_as_staff_user()
        response = self.client.post(reverse(self.view_name), {'q': 'Luis'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertContainsOtherSubs(response)

    def test_get_method_not_allowed(self):
        self.login_as_staff_user()
        response = self.client.get(reverse(self.view_name), {'q': 'Luis'})
        # should return "method not allowed"
        self.assertEqual(response.status_code, 405)

    def test_can_find_app_with_phone_number(self):
        self.login_as_staff_user()
        response = self.client.post(
            reverse(self.view_name), {'q': '2124848'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertContainsOtherSubs(response)

    def test_can_find_app_with_email(self):
        self.login_as_staff_user()
        response = self.client.post(
            reverse(self.view_name), {'q': 'george@fictions'})
        self.assertEqual(response.status_code, 200)
        self.assertContainsTheseSubs(response)
        self.assertContainsComboSub(response)
        self.assertContainsOtherSubs(response)
