from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from datetime import datetime

from unittest.mock import patch, Mock

from intake.tests import mock
from user_accounts.tests.mock import create_fake_auth_models
from intake import models, anonymous_names, validators


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
        self.assertIsNone(submission.first_opened_by_agency())
        self.assertIsNone(submission.last_opened_by_agency())
        self.assertIsNone(submission.last_processed_by_agency())
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

    def test_send_confirmation_messages(self):
        # grab the peferred contact methods
        # try to send the notification
        # notify us of the outcome
        # log the confirmation
        pass

    def test_sent_confirmation_log(self):
        pass


    @patch('intake.models.notifications')
    @patch('intake.models.settings')
    def test_get_unopened_submissions(self, settings, notifications):
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
    def test_mark_viewed(self, notifications):
        submission = mock.FormSubmissionFactory.create()
        submissions = [submission]
        agency_user = self.agency_users[0]
        non_agency_user = self.non_agency_users[0]

        # case: viewed by non agency user
        models.FormSubmission.mark_viewed(submissions, non_agency_user)
        instance = models.FormSubmission.objects.get(pk=submission.id)
        self.assertIsNone(instance.first_opened_by_agency())
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
        self.assertTrue(instance.last_opened_by_agency())
        self.assertTrue(instance.first_opened_by_agency())
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
    @patch('intake.models.User.objects.filter')
    @patch('intake.models.notifications')
    def test_refer_unopened_apps(self, notifications, get_notified_users, get_unopened_apps, ApplicationLogEntry):

        emails = [u.email for u in self.users if u.profile.should_get_notifications]
        get_notified_users.return_value = [Mock(email=email) for email in emails]

        # case: some unopened apps
        submissions = [
            mock.FormSubmissionFactory.build(
                id=i+1, anonymous_name='App')
            for i in range(3)]
        get_unopened_apps.return_value = submissions
        output = models.FormSubmission.refer_unopened_apps()

        notifications.front_email_daily_app_bundle.send.assert_called_once_with(
            to=emails,
            count=3,
            submission_ids=[1,2,3]
            )
        notifications.slack_app_bundle_sent.send.assert_called_once_with(
            emails=emails, submissions=get_unopened_apps.return_value)
        ApplicationLogEntry.log_referred.assert_called_once_with([1,2,3], user=None)
        self.assertEqual(output, notifications.slack_app_bundle_sent.render.return_value)

        # case: no unopened apps
        get_unopened_apps.return_value = []
        notifications.reset_mock()
        ApplicationLogEntry.reset_mock()
        output = models.FormSubmission.refer_unopened_apps()

        notifications.front_email_daily_app_bundle.send.assert_not_called()
        ApplicationLogEntry.log_referred.assert_not_called()
        notifications.slack_app_bundle_sent.send.assert_called_once_with(
            emails=emails, submissions=get_unopened_apps.return_value)
        self.assertEqual(output, notifications.slack_app_bundle_sent.render.return_value)

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
        expected_results = expected_logs
        results = [
            n for n
            in models.FormSubmission.agency_event_logs(
                instance, 1)]
        self.assertListEqual(results, expected_results)

    def test_contact_info_json_field_validation(self):
        # it should not be checking the contact info itself
        # that's it's own bag of problems
        # I'm not ready to validate phone numbers or addresses
        # but that would be cool
        # this should just check if any methods are a valid method
        # but if there is a method, the value must not be empty

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

        invalid_cases = [nonexistent_method, empty_contact_info, *not_dict]
        for invalid_data in invalid_cases:
            with self.assertRaises(ValidationError):
                validators.contact_info_json(
                    invalid_data
                    )




















    
