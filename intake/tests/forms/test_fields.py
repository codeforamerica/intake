from unittest import TestCase


class TestFields(TestCase):

    def test_using_fields_in_set(self):
        from intake.forms import fields

        field_set = {
            fields.ContactInfoFields.contact_preferences,
            fields.CaseStatusFields.us_citizen
        }

        other_set = {
            fields.ContactInfoFields.contact_preferences,
        }

        result = field_set - other_set

        self.assertTrue(result < field_set)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.pop(), fields.CaseStatusFields.us_citizen)