from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from datetime import datetime

from unittest.mock import patch, Mock

from intake.tests import mock
from user_accounts.tests.mock import create_fake_auth_models
from user_accounts import models as auth_models
from intake import models, model_fields, anonymous_names, validators, notifications, constants
from formation.validators import are_valid_choices

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

    def test_all_submissions_have_counties(self):
        all_submissions = models.FormSubmission.all_plus_related_objects()
        for submission in all_submissions:
            counties = submission.counties.all()
            self.assertTrue(list(counties))

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
        contact_preferences = submission.get_nice_contact_preferences()
        for label in ['voicemail', 'text message', 'email', 'paper mail']:
            self.assertIn(label, contact_preferences)
        submission = mock.FormSubmissionFactory.build(answers=prefers_nothing)
        self.assertListEqual([], submission.get_contact_preferences())

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

    @patch('intake.models.FormSubmission.get_unopened_apps')
    @patch('intake.models.User.objects.filter')
    @patch('intake.models.notifications')
    def test_refer_unopened_apps(self, notifications, get_notified_users, get_unopened_apps):

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
        logs = models.ApplicationLogEntry.objects.filter(
            event_type=models.ApplicationLogEntry.REFERRED, submission_id__in=[1,2,3]).all()
        self.assertEqual(len(logs), 3)
        for log in logs:
            self.assertIsNone(log.user)
        self.assertEqual(output, notifications.slack_app_bundle_sent.render.return_value)

        # case: no unopened apps
        get_unopened_apps.return_value = []
        logs.delete()
        notifications.reset_mock()
        output = models.FormSubmission.refer_unopened_apps()

        notifications.front_email_daily_app_bundle.send.assert_not_called()
        logs = models.ApplicationLogEntry.objects.filter(
            event_type=models.ApplicationLogEntry.REFERRED, submission_id__in=[1,2,3]).all()
        self.assertEqual(len(logs), 0)
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
                raise auth_models.Profile.DoesNotExist("no profile for this user")

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

        contact_info_field = model_fields.ContactInfoJSONField(default=dict, blank=True)
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
        submission = mock.FormSubmissionFactory.create()
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

    def test_submission_get_contact_info(self):
        submission = mock.FormSubmissionFactory.build()
        # base case: easy
        submission.answers['contact_preferences'] = ['prefers_email', 'prefers_sms']
        submission.answers['email'] = 'someone@gmail.com'
        submission.answers['phone_number'] = '+19993334444'
        expected = {
            'email': 'someone@gmail.com',
            'sms': '+19993334444'}
        result = submission.get_contact_info()
        self.assertDictEqual(result, expected)

        # case: address
        submission.answers['contact_preferences'] = ['prefers_snailmail']
        submission.answers['address']['street'] = '123 Main St'
        submission.answers['address']['city'] = 'San Francisco'
        submission.answers['address']['state'] = 'CA'
        submission.answers['address']['zip'] = '99999'
        expected = {'snailmail': '123 Main St\nSan Francisco, CA\n99999'}
        result = submission.get_contact_info()
        self.assertDictEqual(result, expected)

        # case: no preference
        submission.answers.pop('contact_preferences')
        expected = {}
        result = submission.get_contact_info()
        self.assertDictEqual(result, expected)


    @patch('intake.models.notifications.slack_confirmation_send_failed.send')
    @patch('intake.models.notifications.slack_confirmation_sent.send')
    @patch('intake.models.notifications.sms_confirmation.send')
    @patch('intake.models.notifications.email_confirmation.send')
    @patch('intake.models.random')
    def test_send_submission_confirmation(self, random, email_notification, sms_notification, sent_notification, slack_failed_notification):
        random.choice.return_value = 'Staff'
        submission = mock.FormSubmissionFactory.create()
        submission.answers['first_name'] = 'Foo'

        # case: all methods all good
        submission.answers['contact_preferences'] = ['prefers_email', 'prefers_sms', 'prefers_snailmail', 'prefers_voicemail']
        submission.answers['email'] = 'someone@gmail.com'
        submission.answers['phone_number'] = '+19993334444'

        submission.send_confirmation_notifications()

        logs = models.ApplicationLogEntry.objects.filter(
            submission=submission,
            event_type=models.ApplicationLogEntry.CONFIRMATION_SENT).all()
        self.assertEqual(len(logs), 2)
        email_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['someone@gmail.com'])
        sms_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['+19993334444'])
        sent_notification.assert_called_once_with(
            submission=submission, methods=['email', 'sms', 'snailmail', 'voicemail'])
        slack_failed_notification.assert_not_called()

        # case: sms fails, email works
        sms_notification.reset_mock()
        email_notification.reset_mock()
        sent_notification.reset_mock()
        logs.delete()
        sms_error = notifications.FrontAPIError('front error')
        sms_notification.side_effect = sms_error
        
        submission.send_confirmation_notifications()
        logs = models.ApplicationLogEntry.objects.filter(
            submission=submission,
            event_type=models.ApplicationLogEntry.CONFIRMATION_SENT).all()
        self.assertEqual(len(logs), 1)
        email_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['someone@gmail.com'])
        sms_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['+19993334444'])
        sent_notification.assert_called_once_with(
            submission=submission, methods=['email', 'snailmail', 'voicemail'])
        slack_failed_notification.assert_called_once_with(
            submission=submission, errors={'sms': sms_error})

        # case: email & sms both fail
        sms_notification.reset_mock()
        email_notification.reset_mock()
        sent_notification.reset_mock()
        slack_failed_notification.reset_mock()
        logs.delete()
        sms_error = notifications.FrontAPIError('sms error')
        email_error = notifications.FrontAPIError('sms error')
        sms_notification.side_effect = sms_error
        email_notification.side_effect = email_error

        submission.send_confirmation_notifications()
        logs = models.ApplicationLogEntry.objects.filter(
            submission=submission,
            event_type=models.ApplicationLogEntry.CONFIRMATION_SENT).all()
        self.assertEqual(len(logs), 0)
        email_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['someone@gmail.com'])
        sms_notification.assert_called_once_with(
            staff_name='Staff', name='Foo', to=['+19993334444'])
        sent_notification.assert_called_once_with(
            submission=submission, methods=['snailmail', 'voicemail'])
        slack_failed_notification.assert_called_once_with(
            submission=submission, errors={'sms': sms_error, 'email': email_error})

    def test_can_get_counties_from_submissions(self):
        submission = mock.FormSubmissionFactory.create()
        counties = list(submission.counties.all())
        mock_field = Mock(
            choices=constants.COUNTY_CHOICES,
            required=True
            )
        slugs = [county.slug for county in counties]
        are_valid_choices.set_context(mock_field)
        are_valid_choices(slugs)
        mock_field.add_error.assert_not_called()


class TestCounty(TestCase):

    def test_county_init(self):
        county = models.County(slug="yolo", description="Yolo County")
        self.assertEqual(county.slug, "yolo")
        self.assertEqual(county.description, "Yolo County")

    def test_get_receiving_agency(self):
        expected_matches = (
            (constants.Counties.SAN_FRANCISCO, "San Francisco Public Defender"),
            (constants.Counties.CONTRA_COSTA, "Contra Costa Public Defender"))
        counties = models.County.objects.all()
        for county_slug, agency_name in expected_matches:
            county = counties.filter(slug=county_slug).first()
            organization = county.get_receiving_agency()
            self.assertEqual(organization.name, agency_name)






















    
