from unittest.mock import Mock, patch
from django.http.request import QueryDict
from django.test import TestCase
from formation.forms import CombinableCountyFormSpec
from formation.combinable_base import FormSpecSelector
from formation import fields as F
from formation.form_base import Form
from intake.services import edit_form_service

validator_a = Mock()
validator_b = Mock()


# Fake Example Form Configuration
class TlonCountyFormSpec(CombinableCountyFormSpec):
    county = 'tlon_county'
    fields = {
        F.FirstName,
        F.EmailField,
        F.AdditionalInformation,
        F.DateOfBirthField,
    }
    required_fields = {
        F.EmailField,
    }
    validators = [validator_a]


class UqbarCountyFormSpec(CombinableCountyFormSpec):
    county = 'uqbar_county'
    fields = {
        F.ContactPreferences,
        F.FirstName,
        F.PhoneNumberField,
        F.ReasonsForApplying
    }
    required_fields = {
        F.FirstName,
        F.PhoneNumberField,
        F.ReasonsForApplying
    }
    validators = [validator_b]


fake_county_form_selector = FormSpecSelector(
    [TlonCountyFormSpec(), UqbarCountyFormSpec()], Form)


def dict_to_querydict(dict_data):
    qdict = QueryDict('', mutable=True)
    for key, value in dict_data.items():
        if isinstance(value, list):
            qdict.setlist(key, value)
        else:
            qdict[key] = value
    return qdict


@patch(
    'intake.services.edit_form_service.county_form_selector',
    fake_county_form_selector)
class TestGetEditFormClassForUserAndSubmission(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_a = Mock(**{
            'is_staff': False,
            'profile.organization.county.slug': 'tlon_county'})
        cls.user_b = Mock(**{
            'is_staff': False,
            'profile.organization.county.slug': 'uqbar_county'})
        cls.staff_user = Mock(is_staff=True)
        cls.sub = Mock()
        cls.sub.organizations.values_list.return_value = [
            'tlon_county', 'uqbar_county']

    def test_staff_user_gets_fields_from_all_orgs(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
            self.staff_user, self.sub)
        self.assertIn(F.FirstName, result.fields)
        self.assertIn(F.EmailField, result.fields)
        self.assertIn(F.ContactPreferences, result.fields)
        self.assertIn(F.PhoneNumberField, result.fields)
        self.assertIn(F.DateOfBirthField, result.fields)

    def test_nonstaff_user_gets_fields_from_own_org(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                    self.user_a, self.sub)
        self.assertIn(F.FirstName, result.fields)
        self.assertIn(F.EmailField, result.fields)
        self.assertIn(F.DateOfBirthField, result.fields)

    def test_nonstaff_user_does_not_get_fields_from_other_org(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                    self.user_a, self.sub)
        self.assertNotIn(F.PhoneNumberField, result.fields)

    def test_nonstaff_user_gets_required_fields_from_all_orgs(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                    self.user_a, self.sub)
        self.assertIn(F.FirstName, result.required_fields)
        self.assertIn(F.EmailField, result.required_fields)

    def test_noneditable_fields_are_excluded(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                    self.staff_user, self.sub)
        self.assertNotIn(F.AdditionalInformation, result.fields)
        self.assertNotIn(F.ReasonsForApplying, result.fields)
        self.assertNotIn(F.AdditionalInformation, result.required_fields)
        self.assertNotIn(F.ReasonsForApplying, result.required_fields)

    def test_result_combines_all_validators(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                            self.staff_user, self.sub)
        self.assertIn(validator_a, result.validators)
        self.assertIn(validator_b, result.validators)

    def test_result_returns_expected_form_class(self):
        result = edit_form_service.get_edit_form_class_for_user_and_submission(
                                    self.user_a, self.sub)
        self.assertTrue(issubclass(result, Form))
        self.assertTrue(hasattr(result, 'fields'))
        self.assertTrue(hasattr(result, 'required_fields'))
        self.assertTrue(hasattr(result, 'validators'))


class TestGetChangedDataFromForm(TestCase):

    def setUp(self):
        super().setUp()
        self.Form = fake_county_form_selector.get_combined_form_class(
            counties=['tlon_county', 'uqbar_county'])

    def test_does_not_return_unchanged_fields(self):
        post_data = dict_to_querydict({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob.year': '1791',
            'dob.month': '2',
            'dob.day': '6',
            'reasons_for_applying': ['pending_job'],
            'existing_first_name': 'Jorge',
            'existing_contact_preferences': ['prefers_email'],
            'existing_phone_number': '1928730983475123',
            'existing_email': 'nothing@nowhere',
            'existing_dob.year': '1791',
            'existing_dob.month': '2',
            'existing_dob.day': '6',
            'existing_reasons_for_applying': ['pending_job']
        })
        form = self.Form(post_data, validate=True)
        self.assertEqual(
            {}, edit_form_service.get_changed_data_from_form(form))

    def test_returns_changed_fields(self):
        post_data = dict_to_querydict({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email', 'prefers_sms'],
            'phone_number': '4152124848',
            'email': 'nothing@nowhere.com',
            'dob.year': '1791',
            'dob.month': '2',
            'dob.day': '6',
            'reasons_for_applying': ['pending_job'],
            'existing_first_name': 'George',
            'existing_contact_preferences': ['prefers_email'],
            'existing_phone_number': '1928730983475123',
            'existing_email': 'nothing@nowhere',
            'existing_dob.year': '1791',
            'existing_dob.month': '2',
            'existing_dob.day': '6',
            'existing_reasons_for_applying': ['pending_job']
        })
        form = self.Form(post_data, validate=True)
        expected_diff = {
            'first_name': {'before': 'George', 'after': 'Jorge'},
            'email': {
                'before': 'nothing@nowhere', 'after': 'nothing@nowhere.com'},
            'phone_number': {
                'after': '(415) 212-4848', 'before': '1928730983475123'},
            'contact_preferences': {
                'after': 'Email or Text Message', 'before': 'Email'}}
        self.assertEqual(
            expected_diff, edit_form_service.get_changed_data_from_form(form))

    def test_returns_changed_multivalue_fields(self):
        post_data = dict_to_querydict({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob.year': '1791',
            'dob.month': '2',
            'dob.day': '6',
            'reasons_for_applying': ['pending_job'],
            'existing_first_name': 'Jorge',
            'existing_contact_preferences': ['prefers_email'],
            'existing_phone_number': '1928730983475123',
            'existing_email': 'nothing@nowhere',
            'existing_dob.year': '1791',
            'existing_dob.month': 'February',
            'existing_dob.day': '6',
            'existing_reasons_for_applying': ['pending_job']
        })
        form = self.Form(post_data, validate=True)
        expected_diff = {
            'dob': {'before': 'February/6/1791', 'after': '2/6/1791'}}
        self.assertEqual(
            expected_diff, edit_form_service.get_changed_data_from_form(form))
