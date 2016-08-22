from unittest import TestCase
from formation.tests.utils import PatchTranslationTestCase, django_only
from unittest.mock import Mock, patch
from formation.tests import mock

from formation.forms import county_form_selector, gave_preferred_contact_methods
from formation import fields as F
from intake.constants import Counties


class TestCombinableFormSpec(PatchTranslationTestCase):

    def test_can_combine_validators(self):
        CombinedForm = county_form_selector.get_combined_form_class(
            counties=[
                Counties.OTHER,
                Counties.SAN_FRANCISCO,
                Counties.CONTRA_COSTA
            ])
        self.assertListEqual(CombinedForm.validators,
                             [gave_preferred_contact_methods]
                             )

    def test_combines_optional_fields_properly(self):
        CombinedForm = county_form_selector.get_combined_form_class(
            counties=[
                Counties.OTHER,
                Counties.SAN_FRANCISCO,
                Counties.CONTRA_COSTA
            ])
        expected_optional_fields = {
            F.HowDidYouHear,
            F.AdditionalInformation
        }
        self.assertTrue(
            expected_optional_fields == set(CombinedForm.optional_fields)
        )
