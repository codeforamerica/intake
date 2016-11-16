import os
from datetime import datetime
from unittest import skipUnless
from unittest.mock import patch, Mock

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


from intake.tests import mock
from user_accounts.tests.mock import create_fake_auth_models
from user_accounts import models as auth_models
from intake import (
    models, anonymous_names, validators, notifications,
    constants)

from formation import field_types


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
        submission = mock.FormSubmissionFactory.create()
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

    def test_all_submissions_have_organizations(self):
        all_submissions = models.FormSubmission.all_plus_related_objects()
        for submission in all_submissions:
            organizations = submission.organizations.all()
            self.assertTrue(list(organizations))

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

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
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
        prefers_everything = {
            'prefers_email': 'yes',
            'prefers_sms': 'yes',
            'prefers_snailmail': 'yes',
            'prefers_voicemail': 'yes',
        }
        prefers_nothing = {}
        submission = mock.FormSubmissionFactory.build(
            answers=prefers_everything)
        contact_preferences = submission.get_nice_contact_preferences()
        for label in ['voicemail', 'text message', 'email', 'paper mail']:
            self.assertIn(label, contact_preferences)
        submission = mock.FormSubmissionFactory.build(answers=prefers_nothing)
        self.assertListEqual([], submission.get_contact_preferences())

    @patch('intake.notifications')
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
        submissions, logs = models.FormSubmission.mark_viewed(
            submissions, agency_user)
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
        submission.answers['contact_preferences'] = [
            'prefers_email', 'prefers_sms']
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

    @patch('intake.notifications.slack_confirmation_send_failed.send')
    @patch('intake.notifications.slack_confirmation_sent.send')
    @patch('intake.notifications.sms_confirmation.send')
    @patch('intake.notifications.email_confirmation.send')
    @patch('intake.models.form_submission.random')
    def test_send_submission_confirmation(self, random, email_notification,
                                          sms_notification, sent_notification,
                                          slack_failed_notification):
        random.choice.return_value = 'Staff'
        submission = mock.FormSubmissionFactory.create()
        submission.answers['first_name'] = 'Foo'

        # case: all methods all good
        submission.answers['contact_preferences'] = [
            'prefers_email', 'prefers_sms',
            'prefers_snailmail', 'prefers_voicemail']
        submission.answers['email'] = 'someone@gmail.com'
        submission.answers['phone_number'] = '+19993334444'

        submission.send_confirmation_notifications()

        logs = models.ApplicationLogEntry.objects.filter(
            submission=submission,
            event_type=models.ApplicationLogEntry.CONFIRMATION_SENT).all()
        self.assertEqual(len(logs), 2)
        self.assertWasCalledOnce(email_notification)
        self.assertWasCalledOnce(sms_notification)
        sent_notification.assert_called_once_with(
            submission=submission,
            methods=['email', 'sms', 'snailmail', 'voicemail'])
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
        self.assertWasCalledOnce(email_notification)
        self.assertWasCalledOnce(sms_notification)
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
        self.assertWasCalledOnce(email_notification)
        self.assertWasCalledOnce(sms_notification)
        sent_notification.assert_called_once_with(
            submission=submission, methods=['snailmail', 'voicemail'])
        slack_failed_notification.assert_called_once_with(
            submission=submission,
            errors={'sms': sms_error, 'email': email_error})


class TestFormSubmission(TestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_1_submission_to_multiple_orgs']

    def get_a_sample_sub(self):
        return models.FormSubmission.objects.filter(
            organizations__slug='a_pubdef').first()

    def test_create_for_counties(self):
        counties = models.County.objects.exclude(
            slug=constants.Counties.ALAMEDA)
        submission = models.FormSubmission.create_for_counties(
            counties, answers={})
        # one and only one org for each county
        for county in counties:
            self.assertEqual(
                submission.organizations.filter(county=county).count(), 1)

    def test_create_for_counties_fails_without_answers(self):
        counties = models.County.objects.all()
        with self.assertRaises(models.MissingAnswersError):
            models.FormSubmission.create_for_counties(counties)

    def test_create_for_organizations(self):
        organizations = auth_models.Organization.objects.all()
        submission = models.FormSubmission.create_for_organizations(
            organizations, answers={})
        orgs_of_sub = submission.organizations.all()
        for org in organizations:
            self.assertIn(org, orgs_of_sub)

    def test_get_counties(self):
        organizations = auth_models.Organization.objects.all()
        # a submission for all organizations
        submission = models.FormSubmission.create_for_organizations(
            organizations, answers={})
        # it should be desitned for all counties
        counties = models.County.objects.order_by('slug').all()
        counties_from_sub = submission.get_counties().order_by('slug').all()
        self.assertListEqual(list(counties), list(counties_from_sub))

    def test_get_permitted_submissions_when_permitted(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        subs = cc_pubdef.submissions.all()
        mock_user = Mock(is_staff=False, **{'profile.organization': cc_pubdef})
        result = models.FormSubmission.get_permitted_submissions(mock_user)
        self.assertListEqual(list(result), list(subs))

    def test_get_permitted_submisstions_when_not_permitted(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        submission = models.FormSubmission.create_for_organizations(
            [cc_pubdef], answers={})
        mock_user = Mock(is_staff=False, **{'profile.organization': sf_pubdef})
        result = models.FormSubmission.get_permitted_submissions(
            mock_user, [submission.id])
        self.assertListEqual(list(result), [])

    def test_get_permitted_submissions_when_staff(self):
        orgs = auth_models.Organization.objects.all()
        for org in orgs:
            models.FormSubmission.create_for_organizations([org], answers={})
        subs = set(models.FormSubmission.objects.all())
        mock_user = Mock(is_staff=True)
        result = models.FormSubmission.get_permitted_submissions(mock_user)
        self.assertEqual(set(result), subs)

    def test_get_transfer_action_returns_dict(self):
        org = Mock(id=1)

        def name(*args):
            return "Other Public Defender"

        org.__str__ = name
        request = Mock()
        request.path = '/applications/bundle/2/'
        request.user.profile.organization.get_transfer_org.return_value = org
        submission = self.get_a_sample_sub()
        expected_result = {
            'url': str(
                "/applications/mark/transferred/"
                "?ids={}"
                "&to_organization_id=1"
                "&next=/applications/bundle/2/".format(submission.id)),
            'display': 'Other Public Defender'
        }
        self.assertDictEqual(
            submission.get_transfer_action(request),
            expected_result)

    def test_get_transfer_action_returns_none(self):
        request = Mock()
        request.user.profile.organization.get_transfer_org.return_value = None
        submission = self.get_a_sample_sub()
        self.assertIsNone(
            submission.get_transfer_action(request))

    def test_qualifies_for_fee_waiver_with_public_benefits(self):
        sub = models.FormSubmission(
            answers=mock.fake.ebclc_answers(
                on_public_benefits=field_types.YES))
        self.assertEqual(sub.qualifies_for_fee_waiver(), True)

    def test_qualifies_for_fee_waiver_with_no_income(self):
        sub = models.FormSubmission(
            answers=mock.fake.ebclc_answers(
                household_size=0,
                monthly_income=0))
        self.assertTrue(sub.qualifies_for_fee_waiver())

    def test_doesnt_qualify_for_fee_waiver_with_income_and_no_benefits(self):
        sub = models.FormSubmission(
            answers=mock.fake.ebclc_answers(
                on_public_benefits=field_types.NO,
                household_size=11)
            )
        sub.answers['monthly_income'] = \
            (constants.FEE_WAIVER_LEVELS[12] / 12) + 1
        self.assertEqual(sub.qualifies_for_fee_waiver(), False)

    def test_doesnt_qualify_for_fee_waiver_without_valid_inputs(self):
        sub = models.FormSubmission(answers={})
        self.assertEqual(sub.qualifies_for_fee_waiver(), None)


class TestCounty(TestCase):

    fixtures = ['organizations']

    def test_county_init(self):
        county = models.County(slug="yolo", description="Yolo County")
        self.assertEqual(county.slug, "yolo")
        self.assertEqual(county.description, "Yolo County")

    def test_get_receiving_agency_with_no_criteria(self):
        expected_matches = (
            (constants.Counties.SAN_FRANCISCO,
                "San Francisco Public Defender"),
            (constants.Counties.CONTRA_COSTA, "Contra Costa Public Defender"))
        counties = models.County.objects.all()
        answers = {}
        for county_slug, agency_name in expected_matches:
            county = counties.filter(slug=county_slug).first()
            organization = county.get_receiving_agency(answers)
            self.assertEqual(organization.name, agency_name)

    def test_get_receiving_agency_alameda_eligible_for_apd(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        eligible_for_apd = dict(monthly_income=2999, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(eligible_for_apd)
        alameda_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        self.assertEqual(result, alameda_pubdef)

    def test_get_receiving_agency_high_income_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        ebclc_high_income = dict(monthly_income=3000, owns_home=field_types.NO)
        result = alameda.get_receiving_agency(ebclc_high_income)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        self.assertEqual(result, ebclc)

    def test_get_receiving_agency_owns_home_alameda_gets_ebclc(self):
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        ebclc_owns_home = dict(monthly_income=2999, owns_home=field_types.YES)
        result = alameda.get_receiving_agency(ebclc_owns_home)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        self.assertEqual(result, ebclc)


class TestFilledPDF(TestCase):

    def test_get_absolute_url(self):
        org = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = models.FormSubmission.create_for_organizations([org], answers={})
        expected_url = "/application/{}/pdf/".format(sub.id)
        filled = models.FilledPDF(submission=sub)
        self.assertEqual(filled.get_absolute_url(), expected_url)

    def test_save_binary_data_to_pdf(self):
        org = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = models.FormSubmission.create_for_organizations([org], answers={})
        data = b'content'
        fob = SimpleUploadedFile(
            content=data, name="content.pdf", content_type="application/pdf")
        filled = models.FilledPDF(submission=sub, pdf=fob)
        filled.save()
        self.assertEqual(filled.pdf.read(), data)
        self.assertIn("content", filled.pdf.name)
        self.assertIn(".pdf", filled.pdf.name)


class TestApplicationBundle(TestCase):

    fixtures = ['organizations']

    def test_should_have_a_pdf_positive(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        mock.fillable_pdf(organization=sf_pubdef)
        sub = models.FormSubmission.create_for_organizations(
                [sf_pubdef], answers={})
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)
        self.assertTrue(bundle.should_have_a_pdf())

    def test_should_have_a_pdf_negative(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = models.FormSubmission.create_for_organizations(
                [cc_pubdef], answers={})
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=cc_pubdef, submissions=[sub], skip_pdf=True)
        self.assertFalse(bundle.should_have_a_pdf())

    def test_get_individual_filled_pdfs(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        subs = [
            models.FormSubmission.create_for_organizations(
                [sf_pubdef], answers={})
            for i in range(2)]
        expected_pdfs = [
            models.FilledPDF(original_pdf=fillable, submission=sub)
            for sub in subs]
        for pdf in expected_pdfs:
            pdf.save()
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=sf_pubdef, submissions=subs, skip_pdf=True)
        query = bundle.get_individual_filled_pdfs().order_by('pk')
        pdfs = list(query)
        self.assertListEqual(pdfs, expected_pdfs)

    def test_get_absolute_url(self):
        org = auth_models.Organization.objects.first()
        bundle = models.ApplicationBundle(
            organization=org)
        bundle.save()
        expected_url = "/applications/bundle/{}/".format(bundle.id)
        result = bundle.get_absolute_url()
        self.assertEqual(result, expected_url)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_calls_pdfparser_correctly(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        subs = [
            models.FormSubmission.create_for_organizations(
                [sf_pubdef],
                answers=mock.fake.cleaned_sf_county_form_answers())
            for i in range(2)]
        pdfs = [fillable.fill_for_submission(sub) for sub in subs]
        parser = models.get_parser()
        result = parser.join_pdfs(filled.pdf for filled in pdfs)
        self.assertTrue(len(result) > 30000)

    def test_build_bundled_pdf_with_no_filled_pdfs(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sub = models.FormSubmission.create_for_organizations(
                [cc_pubdef], answers={})
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=cc_pubdef, submissions=[sub], skip_pdf=True)
        get_pdfs_mock = Mock()
        bundle.get_individual_filled_pdfs = get_pdfs_mock
        bundle.build_bundled_pdf_if_necessary()
        get_pdfs_mock.assert_not_called()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdf_with_one_pdf(self, logger, get_parser, slack):
        # set up associated data
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = models.FormSubmission.create_for_organizations(
                [sf_pubdef], answers={})
        fillable = mock.fillable_pdf(organization=sf_pubdef)
        data = b'content'
        filled = models.FilledPDF.create_with_pdf_bytes(
            pdf_bytes=data, submission=sub, original_pdf=fillable)
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=sf_pubdef, submissions=[sub], skip_pdf=True)

        # set up mocks
        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=[filled])
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs

        # run method
        bundle.build_bundled_pdf_if_necessary()

        # check results
        get_parser.assert_not_called()
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()
        self.assertEqual(bundle.bundled_pdf.read(), data)

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdf_if_has_pdfs(self, logger, get_parser, slack):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        subs = [
            models.FormSubmission.create_for_organizations(
                [sf_pubdef], answers={})
            for i in range(2)]

        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(
            return_value=['pdf' for sub in subs])
        get_parser.return_value.join_pdfs.return_value = b'pdf'

        bundle = models.ApplicationBundle.create_with_submissions(
            organization=sf_pubdef, submissions=subs, skip_pdf=True)
        bundle.should_have_a_pdf = should_have_a_pdf
        bundle.get_individual_filled_pdfs = get_individual_filled_pdfs
        bundle.build_bundled_pdf_if_necessary()
        logger.assert_not_called()
        slack.assert_not_called()
        get_individual_filled_pdfs.assert_called_once_with()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdfs_if_not_prefilled(
            self, logger, get_parser, SimpleUploadedFile, slack):
        should_have_a_pdf = Mock(return_value=True)
        get_individual_filled_pdfs = Mock(return_value=[])
        mock_submissions = Mock(**{'all.return_value': [Mock(), Mock()]})
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        mock_bundle = Mock(
            pk=2,
            should_have_a_pdf=should_have_a_pdf,
            get_individual_filled_pdfs=get_individual_filled_pdfs,
            submissions=mock_submissions)
        mock_bundle.organization.pk = 1

        models.ApplicationBundle.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(len(get_individual_filled_pdfs.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()

    @patch('intake.notifications.slack_simple.send')
    @patch('intake.models.application_bundle.SimpleUploadedFile')
    @patch('intake.models.get_parser')
    @patch('intake.models.application_bundle.logger')
    def test_build_bundled_pdfs_if_some_are_not_prefilled(
            self, logger, get_parser, SimpleUploadedFile, slack):
        should_have_a_pdf = Mock(return_value=True)
        mock_filled_pdf = Mock()
        # one existing pdf
        get_individual_filled_pdfs = Mock(return_value=[mock_filled_pdf])
        # two submissions
        mock_submissions = [Mock(), Mock()]
        mock_submissions_field = Mock(**{'all.return_value': mock_submissions})
        get_parser.return_value.join_pdfs.return_value = b'pdf'
        mock_bundle = Mock(
            pk=2,
            should_have_a_pdf=should_have_a_pdf,
            get_individual_filled_pdfs=get_individual_filled_pdfs,
            submissions=mock_submissions_field)
        mock_bundle.organization.pk = 1
        models.ApplicationBundle.build_bundled_pdf_if_necessary(mock_bundle)
        error_msg = "Submissions for ApplicationBundle(pk=2) lack pdfs"
        logger.error.assert_called_once_with(error_msg)
        slack.assert_called_once_with(error_msg)
        self.assertEqual(len(get_individual_filled_pdfs.mock_calls), 2)
        mock_bundle.save.assert_called_once_with()
        for mock_sub in mock_submissions:
            mock_sub.fill_pdfs.assert_called_once_with()


class TestApplicationLogEntry(TestCase):
    fixtures = [
        'organizations',
        'mock_profiles',
        'mock_2_submissions_to_cc_pubdef',
        ]

    def test_can_log_referral_between_orgs(self):
        from_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        to_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        from_org_user = from_org.profiles.first().user
        answers = mock.fake.alameda_pubdef_answers()
        submission = models.FormSubmission.create_for_organizations(
            organizations=[from_org], answers=answers)
        log = models.ApplicationLogEntry.log_referred_from_one_org_to_another(
            submission.id, to_organization_id=to_org.id, user=from_org_user
            )
        self.assertEqual(log.from_org(), from_org)
        self.assertEqual(log.user, from_org_user)
        self.assertEqual(log.to_org(), to_org)

    def test_log_multiple_creates_application_events_by_default(self):
        # log submissions read
        submissions = models.FormSubmission.objects.all()
        user = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF).profiles.first().user
        applicant_ids = [sub.applicant_id for sub in submissions]
        event_count_before = models.ApplicationEvent.objects.filter(
            applicant_id__in=applicant_ids).count()
        logs = models.ApplicationLogEntry.log_opened(
            [sub.id for sub in submissions], user)
        expected_difference = len(logs)
        event_count_after = models.ApplicationEvent.objects.filter(
            applicant_id__in=applicant_ids).count()
        self.assertEqual(
            event_count_after - event_count_before,
            expected_difference)


class TestApplicant(TestCase):

    def test_can_create_with_nothing(self):
        applicant = models.Applicant()
        applicant.save()
        self.assertTrue(applicant.id)

    def test_can_log_event(self):
        applicant = models.Applicant()
        applicant.save()
        event_name = "im_being_tested"
        event = applicant.log_event(event_name)
        self.assertTrue(event.id)
        self.assertEqual(event.applicant, applicant)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.data, {})

        all_events = list(applicant.events.all())
        self.assertIn(event, all_events)

    def test_can_log_event_with_data(self):
        applicant = models.Applicant()
        applicant.save()
        event_name = "im_being_tested"
        event_data = {"foo": "bar"}
        event = applicant.log_event(event_name, event_data)
        self.assertEqual(event.data, event_data)
