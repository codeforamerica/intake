import os
from datetime import datetime
from unittest import skipUnless
from unittest.mock import Mock

from project.tests.testcases import TestCase
from django.core.exceptions import ValidationError

from intake.tests import factories
from user_accounts.tests.mock import create_fake_auth_models
from user_accounts import models as auth_models
from intake import (
    models, anonymous_names, validators)


DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


class TestModels(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for key, data in create_fake_auth_models().items():
            setattr(cls, key, data)

    def assertWasCalledOnce(self, mock_obj):
        call_list = mock_obj.mock_calls
        self.assertEqual(len(call_list), 1)

    def test_submission(self):
        submission = factories.FormSubmissionFactory.create()
        self.assertEqual(int, type(submission.id))
        self.assertEqual(dict, type(submission.answers))
        self.assertEqual(datetime, type(submission.date_received))
        self.assertTrue(submission.old_uuid)  # just have a truthy result
        anon = submission.get_anonymous_display()
        self.validate_anonymous_name(anon)
        self.assertIsNone(submission.first_opened_by_agency())
        self.assertIsNone(submission.last_opened_by_agency())
        self.assertIsNone(submission.last_processed_by_agency())
        self.assertEqual(
            models.FormSubmission.objects.get(id=submission.id), submission)

    def test_applicationlogentry(self):
        submission = factories.FormSubmissionFactory.create()
        log = models.ApplicationLogEntry.objects.create(
            submission=submission,
            user=self.users[0],
            event_type=models.ApplicationLogEntry.PROCESSED
        )
        self.assertEqual(
            models.ApplicationLogEntry.objects.get(id=log.id), log)

    def validate_anonymous_name(self, name):
        first_name, *last_names = name.split(' ')
        self.assertIn(first_name,
                      anonymous_names.fake_first_names)
        self.assertIn(' '.join(last_names),
                      anonymous_names.fake_last_names)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_fillablepdf(self):
        submission = factories.FormSubmissionFactory.create()
        from django.core.files import File
        sample_pdf_path = 'tests/sample_pdfs/sample_form.pdf'
        pdf = models.FillablePDF(
            name="Sample_pdf",
            pdf=File(open(sample_pdf_path, 'rb')),
            translator='tests.sample_translator.translate'
        )
        fields = pdf.get_pdf_fields()
        self.assertEqual(type(fields), list)
        filled_pdf = pdf.fill(submission)
        self.assertEqual(type(filled_pdf), bytes)

    def test_anonymous_names(self):
        fake_name = anonymous_names.generate()
        self.validate_anonymous_name(fake_name)

    def test_get_contact_preferences(self):
        prefers_everything = {
            'prefers_email': 'yes',
            'prefers_sms': 'yes',
            'prefers_snailmail': 'yes',
            'prefers_voicemail': 'yes',
        }
        prefers_nothing = {}
        submission = factories.FormSubmissionFactory.build(
            answers=prefers_everything)
        contact_preferences = submission.get_nice_contact_preferences()
        for label in ['voicemail', 'text message', 'email', 'paper mail']:
            self.assertIn(label, contact_preferences)
        submission = factories.FormSubmissionFactory.build(
            answers=prefers_nothing)
        self.assertListEqual([], submission.get_contact_preferences())

    def test_agency_event_logs(self):
        instance = Mock()
        agency = Mock(is_receiving_agency=True)
        non_agency = Mock(is_receiving_agency=False)
        agency_user = Mock(**{'profile.organization': agency})
        # notifications should not affect whether they show up here
        agency_user_without_notifications = Mock(
            should_get_notifications=False, **{'profile.organization': agency})
        non_agency_user = Mock(**{'profile.organization': non_agency})
        expected_logs = [
            Mock(event_type=1, user=agency_user),
            Mock(event_type=1, user=agency_user_without_notifications),
        ]
        unexpected_logs = [
            Mock(user=None, event_type=1),
            Mock(user=None, event_type=2),
            Mock(user=non_agency_user, event_type=1),
            Mock(user=non_agency_user, event_type=2),
            Mock(user=agency_user, event_type=2),
            Mock(user=agency_user_without_notifications, event_type=2),
        ]
        instance.logs.all.return_value = unexpected_logs + expected_logs
        results = [
            n for n
            in models.FormSubmission.agency_event_logs(
                instance, 1)]
        self.assertListEqual(results, expected_logs)

    def test_agency_event_logs_handle_user_without_profile(self):
        agency = Mock(is_receiving_agency=True)
        agency_user = Mock(**{'profile.organization': agency})
        instance = Mock()

        class NoProfile:

            @property
            def profile(self):
                raise auth_models.Profile.DoesNotExist(
                    "no profile for this user")

        user_with_no_profile = NoProfile()
        expected_logs = [
            Mock(event_type=1, user=agency_user),
        ]
        unexpected_logs = [
            Mock(user=None, event_type=1),
            Mock(user=None, event_type=2),
            Mock(user=user_with_no_profile, event_type=1),
            Mock(user=user_with_no_profile, event_type=2),
            Mock(user=user_with_no_profile, event_type=2),
            Mock(user=user_with_no_profile, event_type=2),
        ]
        instance.logs.all.return_value = unexpected_logs + expected_logs
        results = [
            n for n
            in models.FormSubmission.agency_event_logs(
                instance, 1)]
        self.assertListEqual(results, expected_logs)

    def test_contact_info_json_field(self):

        contact_info_field = models.fields.ContactInfoJSONField(
            default=dict, blank=True)
        # valid inputs
        empty = {}
        just_email = {'email': 'someone@gmail.com'}
        all_methods = {
            'email': 'someone@gmail.com',
            'sms': '+19993334444',
            'voicemail': '+19993334444',
            'snailmail': '123 Main St\nOakland, CA\n94609'
        }
        # invalid inputs
        nonexistent_method = {'twitter': '@someone'}
        empty_contact_info = {'email': ''}
        not_dict = [[], '', ' ', 10, True, None]

        valid_cases = [empty, just_email, all_methods]
        for valid_data in valid_cases:
            validators.contact_info_json(
                valid_data
            )
            contact_info_field.validate(valid_data, Mock())

        invalid_cases = [nonexistent_method, empty_contact_info, *not_dict]
        for invalid_data in invalid_cases:
            with self.assertRaises(ValidationError):
                validators.contact_info_json(invalid_data)
            with self.assertRaises(ValidationError):
                contact_info_field.validate(invalid_data, Mock())

    def test_applicantcontactedlogentry_model(self):
        submission = factories.FormSubmissionFactory.create()
        sent_to = {'email': 'someone@gmail.com'}
        log = models.ApplicantContactedLogEntry.objects.create(
            submission=submission,
            user=self.users[0],
            event_type=models.ApplicationLogEntry.CONFIRMATION_SENT,
            contact_info=sent_to,
            message_sent="hi good job applying, ttyl")
        retrieved = models.ApplicantContactedLogEntry.objects.get(id=log.id)
        base_instance = models.ApplicationLogEntry.objects.get(id=log.id)
        self.assertEqual(retrieved, log)
        self.assertEqual(base_instance.id, retrieved.id)
        self.assertDictEqual(log.contact_info, sent_to)
        self.assertEqual(retrieved.submission, submission)
        self.assertEqual(retrieved.message_sent, "hi good job applying, ttyl")

    def test_submission_get_preferred_contact_info(self):
        submission = factories.FormSubmissionFactory.build()
        # base case: easy
        submission.answers['contact_preferences'] = [
            'prefers_email', 'prefers_sms']
        submission.answers['email'] = 'someone@gmail.com'
        submission.answers['phone_number'] = '+19993334444'
        expected = {
            'email': 'someone@gmail.com',
            'sms': '+19993334444'}
        result = submission.get_preferred_contact_info()
        self.assertDictEqual(result, expected)

        # case: address
        submission.answers['contact_preferences'] = ['prefers_snailmail']
        submission.answers['address']['street'] = '123 Main St'
        submission.answers['address']['city'] = 'San Francisco'
        submission.answers['address']['state'] = 'CA'
        submission.answers['address']['zip'] = '99999'
        expected = {'snailmail': '123 Main St\nSan Francisco, CA\n99999'}
        result = submission.get_preferred_contact_info()
        self.assertDictEqual(result, expected)

        # case: no preference
        submission.answers.pop('contact_preferences')
        expected = {}
        result = submission.get_preferred_contact_info()
        self.assertDictEqual(result, expected)
