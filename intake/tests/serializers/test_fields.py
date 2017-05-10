from django.test import TestCase
from intake import models
from intake.tests import factories


from intake.serializers.fields import (
    made_a_meaningful_attempt_to_apply,
    ContactInfoByPreferenceField
)


def make_county_form_completed_event(applicant):
    event = models.ApplicationEvent(
        applicant=applicant,
        name=models.ApplicationEvent.APPLICATION_PAGE_COMPLETE,
        data=dict(page_name='CountyApplication'))
    event.save()


def make_error_event(applicant, errors):
    event = models.ApplicationEvent(
        applicant=applicant,
        name=models.ApplicationEvent.APPLICATION_ERRORS,
        data=dict(errors=errors))
    event.save()


class TestMadeAMeaningfulAttemptToApply(TestCase):

    def test_completed_county_form_returns_true(self):
        applicant = factories.ApplicantFactory()
        make_county_form_completed_event(applicant)
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_select_county_only_returns_false(self):
        applicant = factories.ApplicantFactory()
        make_error_event(applicant, dict(counties=['required']))
        self.assertFalse(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_empty_county_form_returns_false(self):
        applicant = factories.ApplicantFactory()
        make_error_event(applicant, dict(first_name=['required']))
        self.assertFalse(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_county_form_without_first_name_returns_true(self):
        applicant = factories.ApplicantFactory()
        make_error_event(applicant, dict(last_name=['required']))
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_empty_forms_with_later_genuine_attempt_returns_true(self):
        applicant = factories.ApplicantFactory()
        make_error_event(applicant, dict(counties=['required']))
        make_error_event(applicant, dict(first_name=['required']))
        make_error_event(applicant, dict(last_name=['required']))
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_empty_forms_with_later_completed_county_form_returns_true(self):
        applicant = factories.ApplicantFactory()
        make_error_event(applicant, dict(counties=['required']))
        make_error_event(applicant, dict(first_name=['required']))
        make_county_form_completed_event(applicant)
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))


class TestContactInfoByPreferenceField(TestCase):

    def test_returns_expected_dictionary_for_each_preference(self):
        answers = dict(
            contact_preferences=[
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail',
                'prefers_email'
            ],
            phone_number='4442223333',
            address=dict(
                street='654 11th St Apt 999',
                city='Oakland',
                state='CA',
                zip='94449'),
            alternate_phone_number='5551114444',
            email='test@gmail.com',
        )
        expected_output = [
            ('sms', '(444) 222-3333'),
            ('email', 'test@gmail.com'),
            ('voicemail', '(444) 222-3333'),
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
            phone_number='4442223333',
            address=dict(
                street='654 11th St Apt 999',
                city='Oakland',
                state='CA',
                zip='94449'),
            alternate_phone_number='5551114444',
            email='test@gmail.com',
        )
        expected_output = [
            ('email', 'test@gmail.com'),
        ]
        results = ContactInfoByPreferenceField(
        ).to_representation(answers)
        self.assertEqual(results, expected_output)

    def test_empty_input_returns_empty_list(self):
        answers = {}
        expected_output = []
        results = ContactInfoByPreferenceField(
        ).to_representation(answers)
        self.assertEqual(results, expected_output)
