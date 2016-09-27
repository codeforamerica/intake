from unittest import TestCase
from formation import fields


class TestHouseholdSizeField(TestCase):

    def test_display_value_is_larger_than_input(self):
        data = {'household_size': 2}
        field = fields.HouseholdSize(data)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), 2)
        self.assertEqual(field.get_display_value(), 3)
