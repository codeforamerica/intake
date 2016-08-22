
from unittest.mock import Mock, patch
from formation.tests import mock
from formation.tests.utils import PatchTranslationTestCase, django_only

from formation import fields


class TestAddressField(PatchTranslationTestCase):

    def test_address_get_display_value(self):
        input_data = {
            'address_street': '1 Main St.',
            'address_city': 'Oakland',
            'address_state': 'CA',
            'address_zip': '94609',
        }
        expected_output = {
            'street': '1 Main St.',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94609'
        }
        expected_display = "1 Main St.\nOakland, CA\n94609"
        field = fields.AddressField(input_data)
        self.assertTrue(field.is_valid())
        self.assertDictEqual(field.get_current_value(), expected_output)
        self.assertEqual(field.get_display_value(), expected_display)
