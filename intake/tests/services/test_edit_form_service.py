from unittest.mock import Mock, patch
from django.test import TestCase
from user_accounts.tests.factories import (
    FakeOrganizationFactory, UserProfileFactory)
from intake.tests.factories import CountyFactory, FormSubmissionFactory
from formation.forms import CombinableCountyFormSpec
from formation.combinable_base import FormSpecSelector
from formation import fields as F
from formation.form_base import Form
from intake.services import edit_form_service

validator_a = Mock()
validator_b = Mock()

### Fake Example Form Configuration
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


class TestHasErrorsOnExistingDataOnly(TestCase):

    def setUp(self):
        super().setUp()
        self.Form = fake_county_form_selector.get_combined_form_class(
            counties=['tlon_county', 'uqbar_county'])

    def test_errors_on_existing_fields_return_true(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        result = edit_form_service.has_errors_on_existing_data_only(form, sub)
        self.assertTrue(result)

    def test_errors_on_edited_fields_return_false(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job'],
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1891', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        result = edit_form_service.has_errors_on_existing_data_only(form, sub)
        self.assertFalse(result)


class TestRemoveErrorsForExistingData(TestCase):

    def setUp(self):
        super().setUp()
        self.Form = fake_county_form_selector.get_combined_form_class(
            counties=['tlon_county', 'uqbar_county'])

    def test_removes_error_from_form_if_existing(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        edit_form_service.remove_errors_for_existing_data(form, sub)
        self.assertFalse(form.errors)

    def test_removes_error_from_field_if_existing(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        edit_form_service.remove_errors_for_existing_data(form, sub)
        self.assertFalse(form.phone_number.errors)
        self.assertFalse(form.email.errors)
        self.assertFalse(form.dob.errors)

    def test_removes_error_from_subfields_if_existing(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        edit_form_service.remove_errors_for_existing_data(form, sub)
        self.assertFalse(form.dob.year.errors)
        self.assertFalse(form.dob.month.errors)
        self.assertFalse(form.dob.day.errors)

    def test_does_not_remove_error_if_field_was_edited(self):
        form = self.Form({
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1791', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        }, validate=True)
        sub = Mock(answers={
            'first_name': 'Jorge',
            'contact_preferences': ['prefers_email'],
            'phone_number': '1928730983475123',
            'email': 'nothing@nowhere',
            'dob': {'year': '1891', 'month': '2', 'day': '6'},
            'reasons_for_applying': ['pending_job']
        })
        edit_form_service.remove_errors_for_existing_data(form, sub)
        self.assertTrue(form.errors)
        self.assertTrue(form.dob.errors)
        self.assertTrue(form.dob.year.errors)
        self.assertTrue(form.dob.month.errors)
        self.assertTrue(form.dob.day.errors)
