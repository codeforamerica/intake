from django.test import TestCase, override_settings
from datetime import datetime

from unittest.mock import patch, Mock

from intake.tests import mock
from user_accounts.tests.mock import create_fake_auth_models
from intake import models, anonymous_names


class TestModels(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for key, models in create_fake_auth_models().items():
            setattr(cls, key, models)

    def test_submission(self):
        submission = mock.FormSubmissionFactory.create()
        self.assertEqual(int, type(submission.id))
        self.assertEqual(dict, type(submission.answers))
        self.assertEqual(datetime, type(submission.date_received))
        self.assertTrue(submission.old_uuid) # just have a truthy result
        anon = submission.get_anonymous_display()
        self.validate_anonymous_name(anon)
        self.assertIsNone(submission.opened_by_agency())
        self.assertIsNone(submission.processed_by_agency())
        self.assertEqual(
            models.FormSubmission.objects.get(id=submission.id), submission)

    def test_applicationlogentry(self):
        submission = mock.FormSubmissionFactory.create()
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

    def test_fillablepdf(self):
        submission = mock.FormSubmissionFactory.create()
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

    @patch('intake.models.notifications')
    @patch('intake.models.settings')
    def test_get_unopened_submissions(self, settings, notifications):
        settings.DEFAULT_AGENCY_USER_EMAIL = self.users[0].email
        submissions = mock.FormSubmissionFactory.create_batch(4)
        group_a, group_b = submissions[:2], submissions[2:]
        models.FormSubmission.mark_viewed(group_a, self.users[0])
        unopened = models.FormSubmission.get_unopened_apps()
        for sub in group_b:
            self.assertIn(sub, unopened)
        for sub in group_a:
            self.assertNotIn(sub, unopened)

        # make sure we get falsey values if all have been opened
        models.FormSubmission.mark_viewed(group_b, self.users[0])
        unopened = models.FormSubmission.get_unopened_apps()
        self.assertFalse(unopened)

    @patch('intake.models.notifications')
    @patch('intake.models.settings')
    def test_mark_viewed(self, settings, notifications):
        submission = mock.FormSubmissionFactory.create()
        submissions = [submission]
        agency_user = self.users[0]
        non_agency_user = self.users[1]
        settings.DEFAULT_AGENCY_USER_EMAIL = agency_user.email

        # case: viewed by non agency user
        models.FormSubmission.mark_viewed(submissions, non_agency_user)
        instance = models.FormSubmission.objects.get(pk=submission.id)
        self.assertIsNone(instance.opened_by_agency())
        logs = instance.logs.all()
        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertEqual(log.user, non_agency_user)
        self.assertEqual(log.submission, submission)
        self.assertEqual(log.event_type, models.ApplicationLogEntry.OPENED)
        notifications.slack_submissions_viewed.send.assert_called_once_with(
            submissions=submissions,
            user=non_agency_user
            )

        # case: viewed by agency user
        notifications.reset_mock()
        submissions, logs = models.FormSubmission.mark_viewed(submissions, agency_user)
        instance = models.FormSubmission.objects.get(pk=submission.id)
        self.assertTrue(instance.opened_by_agency())
        logs = instance.logs.all()
        self.assertEqual(len(logs), 2)
        log = logs[0]
        self.assertEqual(log.user, agency_user)
        self.assertEqual(log.submission, submission)
        self.assertEqual(log.event_type, models.ApplicationLogEntry.OPENED)
        notifications.slack_submissions_viewed.send.assert_called_once_with(
            submissions=submissions,
            user=agency_user
            )

    @patch('intake.models.ApplicationLogEntry')
    @patch('intake.models.FormSubmission.get_unopened_apps')
    @patch('intake.models.notifications')
    @patch('intake.models.settings')
    def test_refer_unopened_apps(self, settings, notifications, get_unopened_apps, ApplicationLogEntry):
        settings.DEFAULT_NOTIFICATION_EMAIL = 'someone@agency.org'

        # case: some unopened apps
        get_unopened_apps.return_value = (Mock(id=i+1) for i in range(3))
        output = models.FormSubmission.refer_unopened_apps()

        expected_message = "Emailed someone@agency.org with a link to 3 unopened applications"
        notifications.front_email_daily_app_bundle.send.assert_called_once_with(
            to=['someone@agency.org'],
            count=3,
            submission_ids=[1,2,3]
            )
        notifications.slack_simple.send.assert_called_once_with(expected_message)
        ApplicationLogEntry.log_referred.assert_called_once_with([1,2,3], user=None)
        self.assertEqual(output, expected_message)

        # case: no unopened apps
        get_unopened_apps.return_value = []
        notifications.reset_mock()
        ApplicationLogEntry.reset_mock()
        output = models.FormSubmission.refer_unopened_apps()

        expected_message = "No unopened applications. Didn't email someone@agency.org"
        notifications.front_email_daily_app_bundle.send.assert_not_called()
        ApplicationLogEntry.log_referred.assert_not_called()
        self.assertEqual(output, expected_message)

    @override_settings(DEFAULT_AGENCY_USER_EMAIL='someone@agency.org')
    def test_agency_event_logs(self):
        instance = Mock()
        expected_log = Mock(user=Mock(email='someone@agency.org'), event_type=1)
        instance.logs.all.return_value = [
            Mock(user=None, event_type=1),
            expected_log,
            Mock(user=Mock(email='else@other.org'), event_type=1),
            Mock(user=Mock(email='someone@agency.org'), event_type=2),
        ]
        expected_results = [expected_log]
        results = [
            n for n
            in models.FormSubmission.agency_event_logs(
                instance, 1)]
        self.assertListEqual(expected_results, results)


















    
