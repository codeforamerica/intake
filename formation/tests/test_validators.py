
from unittest.mock import Mock, patch
from formation.tests import mock
from formation.tests.utils import PatchTranslationTestCase
from formation import validators


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
