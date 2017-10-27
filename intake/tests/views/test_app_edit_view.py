import json
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from easyaudit.models import CRUDEvent
from project.tests.assertions import assertInputHasValue
from formation import fields as F
from intake.tests.factories import FormSubmissionWithOrgsFactory
from user_accounts.tests.factories import app_reviewer, followup_user
from user_accounts.models import Organization
from intake.views.app_edit_view import (
    remove_sensitive_data_from_data_diff, get_emails_to_notify_of_edits)


def dict_to_post_data(raw_input_data):
    post_data = {}
    for key, value in raw_input_data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                post_key = '{}.{}'.format(key, subkey)
                post_data[post_key] = subvalue
                post_data['existing_' + post_key] = subvalue
        else:
            post_data[key] = value
            post_data['existing_' + key] = value
    return post_data


class TestAppEditView(TestCase):
    fixtures = ['counties', 'organizations', 'groups']

    def setUp(self):
        super().setUp()
        self.santa_clara_pubdef = Organization.objects.get(
            slug='santa_clara_pubdef')
        self.fresno_pubdef = Organization.objects.get(
            slug='fresno_pubdef')
        self.sf_pubdef = Organization.objects.get(
            slug='sf_pubdef')
        self.sub = FormSubmissionWithOrgsFactory(
            organizations=[
                self.santa_clara_pubdef, self.fresno_pubdef,
                self.sf_pubdef])
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
            F.DateOfBirthField
        ]

        fresno_unexpected_fields = [
            F.SocialSecurityNumberField,
            F.CitizenshipStatus
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
            F.DateOfBirthField}

        cfa_user_profile = followup_user()
        self.client.login(
            username=cfa_user_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)

        for field in santa_clara_expected_fields | fresno_expected_fields:
            with self.subTest(field=field):
                self.assertContains(response, field.context_key)
                self.assertContains(response, 'existing_' + field.context_key)

    def test_edit_form_contains_existing_data_and_errors(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.sub.answers['email'] = 'notgood@example'
        self.sub.answers['phone_number'] = '5555555555'
        self.sub.answers['alternate_phone_number'] = '5555555555'
        self.sub.answers['dob'] = {
            'month': 'February',
            'day': 3,
            'year': '19714'}
        self.sub.save()
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        self.assertContains(response, self.sub.answers['first_name'])
        self.assertContains(response, self.sub.answers['last_name'])
        assertInputHasValue(response, 'phone_number', '')
        assertInputHasValue(response, 'existing_phone_number', '5555555555')
        assertInputHasValue(response, 'alternate_phone_number', '')
        assertInputHasValue(
            response, 'existing_alternate_phone_number', '5555555555')
        assertInputHasValue(response, 'email', 'notgood@example')
        assertInputHasValue(response, 'existing_email', 'notgood@example')
        assertInputHasValue(response, 'dob.day', '3')
        assertInputHasValue(response, 'existing_dob.day', '3')
        assertInputHasValue(response, 'dob.month', '')
        assertInputHasValue(response, 'existing_dob.month', 'February')
        assertInputHasValue(response, 'dob.year', '19714')
        assertInputHasValue(response, 'existing_dob.year', '19714')

    # submitting the form
    def test_successful_edit_submission_redirects_to_app_detail(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'email': 'something@example.horse'})
        response = self.client.post(self.edit_url, post_data)
        self.assertRedirects(
            response, self.sub.get_absolute_url(),
            fetch_redirect_response=False)

    def test_user_sees_success_flash_and_updated_info_after_submission(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'email': 'something@example.horse'})
        response = self.client.post(
            self.edit_url, post_data, follow=True)
        expected_flash_message = 'Saved new information for Foo Bar'
        self.assertContains(response, expected_flash_message)

    def test_submitting_unchanged_existing_bad_data_is_not_allowed(self):
        # add existing bad data
        self.sub.answers['email'] = 'notgood@example'
        self.sub.save()
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
           response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo', 'last_name': 'Bar'})
        response = self.client.post(self.edit_url, post_data)
        self.assertEqual(200, response.status_code)

    def test_submitting_new_bad_data_is_not_allowed(self):
        self.sub.answers['email'] = 'notgood@example'
        self.sub.save()
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'email': 'notgood@butdifferent'})
        response = self.client.post(self.edit_url, post_data)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context_data['form'].errors)

    def test_deleting_data_required_by_other_orgs_is_not_allowed(self):
        sf_pubdef = app_reviewer('sf_pubdef')
        self.client.login(
            username=sf_pubdef.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'dob.day': '3', 'dob.month': '', 'dob.year': ''})
        response = self.client.post(self.edit_url, post_data)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context_data['form'].errors)

    def test_updating_data_creates_audit_record(self):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo', 'last_name': 'Bar'})
        response = self.client.post(self.edit_url, post_data, follow=True)
        latest_crud_event = CRUDEvent.objects.filter(
            content_type__app_label='intake',
            content_type__model='formsubmission').latest('datetime')
        self.assertEqual(CRUDEvent.UPDATE, latest_crud_event.event_type)
        data = json.loads(latest_crud_event.object_json_repr)[0]['fields']
        self.assertEqual(data['first_name'], 'Foo')
        self.assertEqual(data['last_name'], 'Bar')
        self.assertEqual(data['answers']['first_name'], 'Foo')
        self.assertEqual(data['answers']['last_name'], 'Bar')

    @patch('intake.views.app_edit_view.app_edited_org_email_notification')
    def test_notifies_org_user_with_safe_data_diff(self, notification_patch):
        fresno_profile = app_reviewer('fresno_pubdef')
        santa_clara_profile = app_reviewer('santa_clara_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'driver_license_or_id': '9123462907890387',
            'email': 'something@example.horse'})
        expected_safe_diff = {
            'First name': {'before': self.sub.first_name, 'after': 'Foo'},
            'Last name': {'before': self.sub.last_name, 'after': 'Bar'},
            'Email': {'before': self.sub.email,
                      'after': 'something@example.horse'}
        }
        self.client.post(self.edit_url, post_data)
        notification_patch.send.assert_any_call(
            to=[santa_clara_profile.user.email],
            sender_profile=fresno_profile,
            editor_email=fresno_profile.user.email,
            editor_org_name=fresno_profile.organization.name,
            app_detail_url=self.sub.get_external_url(),
            submission_id=self.sub.id,
            applicant_name='Foo Bar',
            safe_data_diff=expected_safe_diff,
            unsafe_changed_keys=['Driver License/ID'])
        notification_patch.send.assert_any_call(
            to=[fresno_profile.user.email],
            sender_profile=fresno_profile,
            editor_email=fresno_profile.user.email,
            editor_org_name=fresno_profile.organization.name,
            app_detail_url=self.sub.get_external_url(),
            submission_id=self.sub.id,
            applicant_name='Foo Bar',
            safe_data_diff=expected_safe_diff,
            unsafe_changed_keys=['Driver License/ID'])
        self.assertEqual(2, len(notification_patch.send.mock_calls))

    @patch(
        'intake.views.app_edit_view.app_edited_applicant_email_notification')
    @patch(
        'intake.views.app_edit_view.app_edited_applicant_sms_notification')
    def test_notifies_applicant_of_changed_data_at_old_and_new_contact_info(
            self, sms_notification_patch, email_notification_patch):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'driver_license_or_id': '9123462907890387',
            'email': 'something@example.horse',
            'phone_number': '4153016005'})
        self.client.post(self.edit_url, post_data)
        organization = fresno_profile.organization
        expected_changed_fields = ['Driver License/ID', 'Email',
                                   'First name', 'Last name', 'Phone number']
        email_notification_patch.send.assert_any_call(
            to=['something@example.horse'],
            sender_profile=fresno_profile,
            org_contact_info=organization.get_contact_info_message(),
            org_name='the Fresno County Public Defender',
            changed_fields=expected_changed_fields,
            is_old_contact_info=False)

        email_notification_patch.send.assert_any_call(
            to=[self.sub.email],
            sender_profile=fresno_profile,
            org_contact_info=organization.get_contact_info_message(),
            org_name='the Fresno County Public Defender',
            changed_fields=expected_changed_fields,
            is_old_contact_info=True)
        self.assertEqual(2, len(email_notification_patch.send.mock_calls))

        sms_notification_patch.send.assert_any_call(
            to=['(415) 212-4848'],
            org_contact_info=organization.get_contact_info_message(),
            org_name='the Fresno County Public Defender',
            changed_fields=expected_changed_fields,
            is_old_contact_info=True)

        sms_notification_patch.send.assert_any_call(
            to=['4153016005'],
            org_contact_info=organization.get_contact_info_message(),
            org_name='the Fresno County Public Defender',
            changed_fields=expected_changed_fields,
            is_old_contact_info=False)
        self.assertEqual(2, len(sms_notification_patch.send.mock_calls))

    @patch(
        'intake.views.app_edit_view.app_edited_applicant_email_notification')
    @patch(
        'intake.views.app_edit_view.app_edited_applicant_sms_notification')
    def test_does_not_send_notifications_if_contact_info_does_not_exist(
            self, sms_notification_patch, email_notification_patch):
        self.sub.email = ''
        self.sub.phone_number = ''
        self.sub.answers['email'] = ''
        self.sub.answers['phone_number'] = ''
        self.sub.answers['contact_preferences'] = []
        self.sub.save()
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        post_data.update({
            'first_name': 'Foo',
            'last_name': 'Bar',
            'phone_number': '4153016005'
        })

        self.client.post(self.edit_url, post_data)
        organization = fresno_profile.organization
        expected_changed_fields = ['First name', 'Last name', 'Phone number']
        email_notification_patch.send.assert_not_called()
        sms_notification_patch.send.assert_called_once_with(
            to=['4153016005'],
            org_contact_info=organization.get_contact_info_message(),
            org_name='the Fresno County Public Defender',
            changed_fields=expected_changed_fields,
            is_old_contact_info=False
        )

    @patch('intake.views.app_edit_view.app_edited_org_email_notification')
    @patch(
        'intake.views.app_edit_view.app_edited_applicant_email_notification')
    def test_does_not_notify_if_unchanged(
            self, applicant_notification_patch, org_notification_patch):
        fresno_profile = app_reviewer('fresno_pubdef')
        self.client.login(
            username=fresno_profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(self.edit_url)
        post_data = dict_to_post_data(
            response.context_data['form'].raw_input_data)
        self.client.post(self.edit_url, post_data)
        org_notification_patch.assert_not_called()
        applicant_notification_patch.assert_not_called()


class TestRemoveSensitiveDataFromDataDiff(TestCase):

    def test_removes_unsafe_field_data(self):
        secrets = {
            'SSN': {
                'before': 'super secret',
                'after': 'still very secret',
            },
            'Driver License/ID': {
                'before': 'super secret',
                'after': 'still very secret',
            },
        }
        not_so_secrets = {
            'Email': {
                'before': 'not really an email',
                'after': 'just benign pii',
            },
            'Phone number': {
                'before': 'not really an email',
                'after': 'just benign pii',
            },
        }
        secrets_keys = ['SSN', 'Driver License/ID']
        data_in = dict(**secrets, **not_so_secrets)
        safe_diff_results, secret_keys_results = \
            remove_sensitive_data_from_data_diff(data_in)
        self.assertEqual(not_so_secrets, safe_diff_results)
        self.assertEqual(set(secrets_keys), set(secret_keys_results))


class TestGetUsersToNotifyOfEdits(TestCase):

    fixtures = ['counties', 'organizations', 'groups']

    def test_only_gets_correct_emails(self):
        # users who shouldn't get notifications at an org that would
        fresno_user_w_notifications = app_reviewer('fresno_pubdef')
        fresno_user_without_notifications = app_reviewer(
            'fresno_pubdef', username='fresno_dont_notify')
        fresno_user_without_notifications.should_get_notifications = False
        fresno_user_without_notifications.save()
        santa_clara_user = app_reviewer('santa_clara_pubdef')
        app_reviewer('sf_pubdef')
        submission = FormSubmissionWithOrgsFactory(
            organizations=[
                santa_clara_user.organization,
                fresno_user_w_notifications.organization])
        resulting_emails = set(get_emails_to_notify_of_edits(submission.id))
        expected_emails = {
            fresno_user_w_notifications.user.email,
            santa_clara_user.user.email}
        self.assertEqual(expected_emails, resulting_emails)
