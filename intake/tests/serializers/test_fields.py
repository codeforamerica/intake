from django.test import TestCase
from intake.serializers.fields import ContactInfoByPreferenceField


class TestContactInfoByPreferenceField(TestCase):

    def test_returns_expected_dictionary_for_each_preference(self):
        answers = dict(
            contact_preferences=[
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail',
                'prefers_email'
            ],
            phone_number='4153016005',
            address=dict(
                street='654 11th St Apt 999',
                city='Oakland',
                state='CA',
                zip='94449'),
            alternate_phone_number='4153016005',
            email='test@gmail.com',
        )
        expected_output = [
            ('sms', '(415) 301-6005'),
            ('email', 'test@gmail.com'),
            ('voicemail', '(415) 301-6005'),
            ('snailmail', '654 11th St Apt 999, Oakland, CA 94449'),
        ]
        results = ContactInfoByPreferenceField(
        ).to_representation(answers)
        for key, value in results:
            self.assertTrue(hasattr(value, '__html__'))
        self.assertEqual(results, expected_output)

    def test_doesnt_return_contact_info_if_not_preferred(self):
        answers = dict(
            contact_preferences=[
                'prefers_email'
            ],
            phone_number='4153016005',
            address=dict(
                street='654 11th St Apt 999',
                city='Oakland',
                state='CA',
                zip='94449'),
            alternate_phone_number='4153016005',
            email='test@gmail.com',
        )
        expected_output = [
            ('email', 'test@gmail.com'),
        ]
        results = ContactInfoByPreferenceField().to_representation(answers)
        self.assertEqual(results, expected_output)

    def test_empty_input_returns_empty_list(self):
        answers = {}
        expected_output = []
        results = ContactInfoByPreferenceField(
        ).to_representation(answers)
        self.assertEqual(results, expected_output)
