from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from formation import fields as F
from intake.tests.factories import FormSubmissionWithOrgsFactory
from user_accounts.tests.factories import app_reviewer, followup_user
from user_accounts.models import Organization


def dict_to_post_data(cleaned_data):
    post_data = {}
    for key, value in cleaned_data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                post_key = '{}.{}'.format(key, subkey)
                post_data[post_key] = subvalue
        else:
            post_data[key] = value
    return post_data


class TestAppEditView(TestCase):
    fixtures = ['counties', 'organizations', 'groups']

    def setUp(self):
        super().setUp()
        self.santa_clara_pubdef = Organization.objects.get(
            slug='santa_clara_pubdef')
        self.fresno_pubdef = Organization.objects.get(
            slug='fresno_pubdef')
        self.sub = FormSubmissionWithOrgsFactory(
            organizations=[self.santa_clara_pubdef, self.fresno_pubdef])
        self.edit_url = self.sub.get_edit_url()

    # access control
    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(302, response.status_code)
        self.assertIn(
            reverse('user_accounts-login'), response.url)

    def test_incorrect_org_user_gets_404(self):
        different_org_user_profile = app_reviewer('a_pubdef')
        self.client.login(
            username=different_org_user_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertEqual(404, response.status_code)

    def test_matching_org_user_gets_200(self):
        matching_org_user_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=matching_org_user_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertEqual(200, response.status_code)

    def test_cfa_user_gets_200(self):
        cfa_user_profile = followup_user()
        self.client.login(
            username=cfa_user_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertEqual(200, response.status_code)

    # getting the form
    def test_org_user_gets_expected_form_for_their_org(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)

        fresno_expected_fields = [
            F.ContactPreferences,
            F.FirstName,
            F.MiddleName,
            F.LastName,
            F.Aliases,
            F.PhoneNumberField,
            F.AlternatePhoneNumberField,
            F.AddressField,
            F.DriverLicenseOrIDNumber,
            F.EmailField,
            F.DateOfBirthField,
            F.CaseNumber
        ]

        fresno_unexpected_fields = [
            F.SocialSecurityNumberField,
            F.USCitizen
        ]

        for field in fresno_expected_fields:
            with self.subTest(field=field):
                self.assertContains(response, field.context_key)

        for field in fresno_unexpected_fields:
            with self.subTest(field=field):
                self.assertNotContains(response, field.context_key)
        self.client.logout()

        santa_clara_profile = app_reviewer('santa_clara_pubdef')
        self.client.login(
            username=santa_clara_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)

        santa_clara_expected_fields = [
            F.ContactPreferences,
            F.FirstName,
            F.MiddleName,
            F.LastName,
            F.PhoneNumberField,
            F.AlternatePhoneNumberField,
            F.AddressField,
            F.EmailField,
            F.DateOfBirthField
        ]

        santa_clara_unexpected_fields = [
            F.SocialSecurityNumberField,
            F.Aliases,
            F.DriverLicenseOrIDNumber,
            F.CaseNumber,
            F.MonthlyIncome
        ]

        for field in santa_clara_expected_fields:
            with self.subTest(field=field):
                self.assertContains(response, field.context_key)

        for field in santa_clara_unexpected_fields:
            with self.subTest(field=field):
                self.assertNotContains(response, field.context_key)

    def test_cfa_user_gets_expected_form(self):
        santa_clara_expected_fields = {
            F.ContactPreferences,
            F.FirstName,
            F.MiddleName,
            F.LastName,
            F.PhoneNumberField,
            F.AlternatePhoneNumberField,
            F.AddressField,
            F.EmailField,
            F.DateOfBirthField}
        fresno_expected_fields = {
            F.ContactPreferences,
            F.FirstName,
            F.MiddleName,
            F.LastName,
            F.Aliases,
            F.PhoneNumberField,
            F.AlternatePhoneNumberField,
            F.AddressField,
            F.DriverLicenseOrIDNumber,
            F.EmailField,
            F.DateOfBirthField,
            F.CaseNumber}

        cfa_user_profile = followup_user()
        self.client.login(
            username=cfa_user_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)

        for field in santa_clara_expected_fields | fresno_expected_fields:
            with self.subTest(field=field):
                self.assertContains(response, field.context_key)

    def test_edit_form_starts_prefilled_with_existing_data(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertContains(response, self.sub.answers['first_name'])
        self.assertContains(response, self.sub.answers['last_name'])

    def test_edit_form_does_not_show_validation_errors_for_existing_data(self):
        self.sub.answers['email'] = 'notgood@example'
        self.sub.save()
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertNotContains(response, 'errorlist')

    # submitting the form
    def test_successful_edit_submission_redirects_to_app_detail(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        existing_data = response.context_data['form'].cleaned_data
        existing_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'email': 'something@example.horse'})
        response = self.client.post(
            self.edit_url, dict_to_post_data(existing_data))
        self.assertRedirects(
            response, self.sub.get_absolute_url(), fetch_redirect_response=False)

    def test_user_sees_success_flash_and_updated_info_after_submission(self):
        pass

    def test_submitting_unchanged_existing_bad_data_is_allowed(self):
        pass

    def test_submitting_new_bad_data_is_not_allowed(self):
        pass

    def test_deleting_data_required_by_other_orgs_is_not_allowed(self):
        pass

    def test_updating_data_creates_audit_record(self):
        pass
