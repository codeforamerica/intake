from formation.tests.utils import PatchTranslationTestCase

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


class TestMonthlyIncomeField(PatchTranslationTestCase):

    def test_unreasonable_monthly_wage_makes_warning(self):
        high, low = ("$60,000", "1.543")
        for input_data in (high, low):
            data = {'monthly_income': input_data}
            field = fields.MonthlyIncome(data)
            field.is_valid()
            self.assertTrue(field.warnings)

    def test_reasonable_monthly_wage_is_cool(self):
        data = {'monthly_income': "2,000"}
        field = fields.MonthlyIncome(data)
        field.is_valid()
        self.assertFalse(field.warnings)
