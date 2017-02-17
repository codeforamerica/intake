from unittest.mock import Mock, patch
from formation.tests import mock
from formation.tests.utils import PatchTranslationTestCase
import formation


class TestValidChoiceValidator(PatchTranslationTestCase):

    def test_raises_error_if_no_choices_on_context(self):
        # use with a CharField
        pass

    def test_no_errors_if_empty_and_not_required(self):
        pass

    def test_errors_if_required_and_empty(self):
        pass

    def test_errors_if_invalid_choice(self):
        pass

    def test_creates_expected_error_message(self):
        pass

    def test_creates_expected_possible_choices(self):
        pass


class TestMultipleValidChoiceValidator(PatchTranslationTestCase):

    def test_creates_expected_error_message(self):
        pass

    def test_raises_error_if_not_choices_on_context(self):
        pass

    def test_errors_for_any_invalid_choices(self):
        pass


class EmailAndPhoneForm(formation.form_base.Form):
    fields = [
        formation.fields.PhoneNumberField,
        formation.fields.EmailField
    ]
    validators = [
        formation.validators.at_least_email_or_phone
    ]


class TestAtLeastEmailOrTextValidator(PatchTranslationTestCase):

    def test_valid_if_both_values(self):
        form = EmailAndPhoneForm(dict(
            email='hello@nowhere.com',
            phone_number='415-444-4444'
        ))
        self.assertTrue(form.is_valid())

    def test_valid_if_missing_only_email(self):
        form = EmailAndPhoneForm(dict(
            phone_number='415-444-4444'
        ))
        self.assertTrue(form.is_valid())

    def test_valid_if_missing_only_phone(self):
        form = EmailAndPhoneForm(dict(
            email='hello@nowhere.com'
        ))
        self.assertTrue(form.is_valid())

    def test_errors_if_missing_both(self):
        form = EmailAndPhoneForm({})
        self.assertFalse(form.is_valid())
        expected_errors = {
            key: [formation.validators.AtLeastEmailOrPhoneValidator.message]
            for key
            in formation.validators.AtLeastEmailOrPhoneValidator.field_keys
        }
        self.assertDictEqual(form.errors, expected_errors)
