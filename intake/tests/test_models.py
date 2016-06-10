from django.test import TestCase
from datetime import datetime

from intake.tests import mock
from user_accounts.tests.mock import create_fake_auth_models
from intake import models, anonymous_names


class TestModels(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for key, models in create_fake_auth_models().items():
            setattr(cls, key, models)

    def test_submission(self):
        submission = mock.FormSubmissionFactory.create()
        self.assertEqual(int, type(submission.id))
        self.assertEqual(dict, type(submission.answers))
        self.assertEqual(datetime, type(submission.date_received))
        self.assertEqual(submission.old_uuid, '')
        anon = submission.get_anonymous_display()
        self.validate_anonymous_name(anon)
        for field_name in ('reviewed_by_staff',
            'confirmation_sent',
            'submitted_to_agency', 'opened_by_agency', 'processed_by_agency',
            'due_for_followup', 'followup_sent', 'followup_answered',
            'told_eligible', 'told_ineligible'):
            self.assertIsNone(
                getattr(submission, field_name))
        self.assertEqual(
            models.FormSubmission.objects.get(id=submission.id), submission)

    def test_applicationlogentry(self):
        submission = mock.FormSubmissionFactory.create()
        log = models.ApplicationLogEntry.objects.create(
            submission=submission,
            user=self.users[0],
            action_type=models.ApplicationLogEntry.UPDATED,
            updated_field='reviewed_by_staff'
            )
        self.assertEqual(
            models.ApplicationLogEntry.objects.get(id=log.id), log)

    def validate_anonymous_name(self, name):
        first_name, *last_names = name.split(' ')
        self.assertIn(first_name,
            anonymous_names.fake_first_names)
        self.assertIn(' '.join(last_names), 
            anonymous_names.fake_last_names)


    def test_fillablepdf(self):
        from django.core.files import File
        sample_pdf_path = 'tests/sample_pdfs/sample_form.pdf'
        pdf = models.FillablePDF(
            name="Sample_pdf",
            pdf=File(open(sample_pdf_path, 'rb')),
            translator='tests.sample_translator.translate'
            )
        fields = pdf.get_pdf_fields()
        self.assertEqual(type(fields), list)
        filled_pdf = pdf.fill({'first_name': 'Ben'})
        self.assertEqual(type(filled_pdf), bytes)

    def test_anonymous_names(self):
        fake_name = anonymous_names.generate()
        self.validate_anonymous_name(fake_name)

    def test_get_contact_preferences(self):
        base_answers = mock.fake.sf_county_form_answers()
        prefers_everything = {
            'prefers_email': 'yes',
            'prefers_sms': 'yes',
            'prefers_snailmail': 'yes',
            'prefers_voicemail': 'yes',
        }
        prefers_nothing = {}
        submission = mock.FormSubmissionFactory.build(answers=prefers_everything)
        contact_preferences = submission.get_contact_preferences()
        for label in ['voicemail', 'text message', 'email', 'paper mail']:
            self.assertIn(label, contact_preferences)
        submission = mock.FormSubmissionFactory.build(answers=prefers_nothing)
        self.assertListEqual([], submission.get_contact_preferences())

    def test_get_unopened_submissions(self):
        submissions = mock.FormSubmissionFactory.create_batch(4)
        group_a, group_b = submissions[:2], submissions[2:]
        models.FormSubmission.mark_opened_by_agency(group_a, self.users[0])
        unopened = models.FormSubmission.get_unopened_apps()
        for sub in group_b:
            self.assertIn(sub, unopened)
        for sub in group_a:
            self.assertNotIn(sub, unopened)


    
