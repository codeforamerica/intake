from django.test import TestCase
from markupsafe import escape
from formation import fields
from intake import models


class TestAddressField(TestCase):

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


class TestMonthlyIncomeField(TestCase):

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


class TestMonth(TestCase):

    def test_incorrect_month_number_is_invalid(self):
        data = {'month': 40}
        field = fields.Month(data)
        field.is_valid()
        self.assertTrue(field.errors)
        self.assertIn("Please enter a month between 1 and 12",
                      field.get_errors_list())


class TestDay(TestCase):

    def test_incorrect_day_number_is_invalid(self):
        data = {'day': 102}
        field = fields.Day(data)
        field.is_valid()
        self.assertTrue(field.errors)
        self.assertIn("Please enter a day between 1 and 31",
                      field.get_errors_list())


class TestYear(TestCase):

    def test_incorrect_year_number_is_invalid(self):
        data = {'year': 87}
        field = fields.Year(data)
        field.is_valid()
        self.assertTrue(field.errors)
        self.assertIn("Please enter a year between 1900 and 2017",
                      field.get_errors_list())


class TestDateOfBirthField(TestCase):

    def test_display_value_uses_raw_value_if_non_integer(self):
        data = {
            'dob': {
                'year': 'foo',
                'month': 134,
                'day': False
            }
        }

        field = fields.DateOfBirthField(data)
        field.is_valid()
        self.assertEqual(field.get_display_value(), "134/False/foo")


class TestCounties(TestCase):

    fixtures = ['counties']

    def test_labels_when_rendered(self):
        field = fields.Counties(
            {'counties': ['alameda', 'contracosta']})
        self.assertTrue(field.is_valid())
        contracosta = models.County.objects.get(slug='contracosta')
        html = field.render()
        self.assertIn(escape(contracosta.description), html)

    def test_display_value_when_rendered(self):
        field = fields.Counties(
            {'counties': ['not_listed', 'contracosta']})
        # 'not_listed' is a possible but not valid choice
        self.assertFalse(field.is_valid())
        contracosta = models.County.objects.get(slug='contracosta')
        html = field.render(display=True)
        self.assertIn(escape(contracosta.name), html)
        self.assertNotIn(contracosta.description, html)

    def test_display_value_with_not_listed_override(self):
        field = fields.Counties(
            {'counties': ['not_listed', 'contracosta']})
        # 'not_listed' is a possible but not valid choice
        self.assertFalse(field.is_valid())
        not_listed = models.County.objects.get(slug='not_listed')
        value = field.get_display_value(
            unlisted_counties='Some Counties')
        self.assertIn('Some Counties', value)
        self.assertNotIn(not_listed.description, value)
        self.assertNotIn(not_listed.name, value)
