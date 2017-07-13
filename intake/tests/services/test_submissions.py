import logging
from unittest.mock import Mock, patch
from django.test import TestCase
import intake.services.submissions as SubmissionsService
from intake.tests import mock, factories
from intake.tests.mock_org_answers import get_answers_for_orgs
from intake.tests.base_testcases import ExternalNotificationsPatchTestCase
from formation.forms import county_form_selector
from intake.constants import (
    COUNTY_CHOICE_DISPLAY_DICT, Organizations,
    EMAIL, SMS)
from intake.models import FormSubmission
from intake import constants, models
from user_accounts.models import Organization
from project.tests.assertions import assertInLogsCount

"""
Each function in intake.services.submissions corresponds to a TestCase in this
file.
"""


ALL_COUNTY_SLUGS = list(COUNTY_CHOICE_DISPLAY_DICT.keys())


class TestCreateSubmissions(TestCase):

    fixtures = [
        'counties', 'organizations',
    ]

    def test_can_create_with_form_orgs_and_app_id(self):
        # given an applicant, some orgs, and a validated form
        applicant = factories.ApplicantFactory()
        organizations = list(Organization.objects.all()[:2])
        Form = county_form_selector.get_combined_form_class(
            counties=ALL_COUNTY_SLUGS)
        form = Form(mock.fake.all_county_answers(), validate=True)
        # make a submission
        submission = SubmissionsService.create_submission(
            form, organizations, applicant.id)
        self.assertEqual(submission.applicant_id, applicant.id)
        self.assertEqual(
            set(submission.organizations.all()),
            set(organizations))

    def test_create_sub_with_existing_duplicate(self):
        applicant = factories.ApplicantFactory()
        answers = mock.fake.all_county_answers()
        org = Organization.objects.filter(is_receiving_agency=True).first()
        Form = county_form_selector.get_combined_form_class(
            counties=ALL_COUNTY_SLUGS)
        form = Form(answers, validate=True)
        a = SubmissionsService.create_submission(form, [org], applicant.id)
        self.assertFalse(a.duplicate_set_id)
        answers['last_name'] += 's'
        form = Form(answers, validate=True)
        b = SubmissionsService.create_submission(form, [org], applicant.id)
        self.assertTrue(b.duplicate_set_id)
        dup_set_subs = list(b.duplicate_set.submissions.all())
        for sub in (a, b):
            self.assertIn(sub, dup_set_subs)


class TestGetPermittedSubmissions(TestCase):

    fixtures = [
        'counties', 'organizations', 'groups',
        'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
    ]

    def test_filters_to_organization_of_user(self):
        # Given a user from one org who tries to access all submissions
        # assert that they only receive submissions for their org

        # given a user from one org
        org = Organization.objects.get(slug=Organizations.ALAMEDA_PUBDEF)
        user = org.profiles.first().user
        # who requests all submissions
        submissions = list(SubmissionsService.get_permitted_submissions(user))
        # make sure they only receive those subs targeted to their org
        for sub in submissions:
            orgs = list(sub.organizations.all())
            self.assertIn(org, orgs)
        other_submissions = models.FormSubmission.objects.exclude(
            organizations=org)
        for other in other_submissions:
            self.assertNotIn(other, submissions)


class TestHaveSameOrgs(TestCase):

    fixtures = [
        'counties', 'organizations', 'groups', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
    ]

    def test_returns_false_when_orgs_are_different(self):
        a = FormSubmission.objects.filter(
            organizations__slug=Organizations.ALAMEDA_PUBDEF).first()
        b = FormSubmission.objects.filter(
            organizations__slug=Organizations.COCO_PUBDEF).first()
        self.assertEqual(SubmissionsService.have_same_orgs(a, b), False)

    def test_returns_true_when_orgs_are_the_same(self):
        subs = FormSubmission.objects.filter(
            organizations__slug=Organizations.ALAMEDA_PUBDEF)
        a, b = list(subs)[:2]
        self.assertEqual(SubmissionsService.have_same_orgs(a, b), True)

    def test_returns_false_when_orgs_dont_overlap(self):
        a = FormSubmission.objects.filter(
            organizations__slug=Organizations.ALAMEDA_PUBDEF).first()
        b = FormSubmission.objects.filter(
            organizations__slug=Organizations.COCO_PUBDEF).first()
        cc_pubdef = Organization.objects.get(slug=Organizations.COCO_PUBDEF)
        a.organizations.add_orgs_to_sub(cc_pubdef)
        self.assertEqual(SubmissionsService.have_same_orgs(a, b), False)


class TestFindDuplicates(TestCase):

    fixtures = [
        'counties', 'organizations',
    ]

    def test_finds_subs_with_similar_names(self):
        org = Organization.objects.get(slug=Organizations.ALAMEDA_PUBDEF)
        a_name = dict(
            first_name="Joe",
            middle_name="H",
            last_name="Parabola")
        b_name = dict(
            first_name="Joe",
            middle_name="H",
            last_name="Parabole")
        a = factories.FormSubmissionWithOrgsFactory.create(
            answers=get_answers_for_orgs(
                [org],
                **a_name),
            organizations=[org],
        )
        b = factories.FormSubmissionWithOrgsFactory.create(
            answers=get_answers_for_orgs(
                [org],
                **b_name),
            organizations=[org],
        )
        c = factories.FormSubmissionWithOrgsFactory.create(
            answers=get_answers_for_orgs(
                [org],
                **b_name),
            organizations=[org],
        )
        dups = SubmissionsService.find_duplicates(
            FormSubmission.objects.all())
        pair = dups[0]
        for sub in (a, b, c):
            self.assertIn(sub, pair)

    def test_doesnt_pair_subs_with_differing_names(self):
        org = Organization.objects.get(slug=Organizations.ALAMEDA_PUBDEF)
        a_name = dict(
            first_name="Joe",
            middle_name="H",
            last_name="Parabola")
        b_name = dict(
            first_name="Joseph",
            middle_name="H",
            last_name="Conic Intersection")
        factories.FormSubmissionWithOrgsFactory.create(
            answers=get_answers_for_orgs(
                [org],
                **a_name),
            organizations=[org],
        )
        factories.FormSubmissionWithOrgsFactory.create(
            answers=get_answers_for_orgs(
                [org],
                **b_name),
            organizations=[org],
        )
        dups = SubmissionsService.find_duplicates(
            FormSubmission.objects.all())
        self.assertFalse(dups)


class TestGetConfirmationFlashMessages(TestCase):

    def make_mock_confirmation_notification(self, successes, **contact_info):
        """contact_info and successes
        """
        notification = Mock()
        notification.contact_info = contact_info
        notification.successes = successes
        return notification

    def test_messages_for_full_success(self):
        confirmation = self.make_mock_confirmation_notification(
            successes=[EMAIL, SMS],
            email="test@test.com",
            sms="(555) 444-2222")
        expected = [
            "We've sent you an email at test@test.com",
            "We've sent you a text message at (555) 444-2222",
        ]
        result = SubmissionsService.get_confirmation_flash_messages(
            confirmation)
        self.assertEqual(result, expected)

    def test_messages_with_no_usable_contact_info(self):
        confirmation = self.make_mock_confirmation_notification(
            successes=[],
            snailmail="111 Main St.",
            voicemail="(555) 444-2222")
        expected = []
        result = SubmissionsService.get_confirmation_flash_messages(
            confirmation)
        self.assertEqual(result, expected)


class TestSendConfirmationNotifications(ExternalNotificationsPatchTestCase):

    fixtures = [
        'counties',
        'organizations'
    ]

    def get_orgs(self):
        return [Organization.objects.get(slug=Organizations.ALAMEDA_PUBDEF)]

    def test_notifications_slacks_and_logs_for_full_contact_preferences(self):
        applicant = factories.ApplicantFactory()
        answers = get_answers_for_orgs(
            self.get_orgs(),
            contact_preferences=[
                'prefers_email',
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'
            ],
            email='test@gmail.com',
            phone_number='5554442222',
        )
        sub = factories.FormSubmissionWithOrgsFactory.create(
            applicant=applicant,
            organizations=self.get_orgs(),
            answers=answers)
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 1)
        assertInLogsCount(logs, {'event_name=app_confirmation_sent': 1})

    def test_notifications_slacks_and_logs_for_no_contact_preferences(self):
        applicant = factories.ApplicantFactory()
        answers = get_answers_for_orgs(
            self.get_orgs(),
            contact_preferences=[],
            email='test@gmail.com',
            phone_number='5554442222',
        )
        sub = factories.FormSubmissionWithOrgsFactory.create(
            applicant=applicant,
            organizations=self.get_orgs(),
            answers=answers)
        # does not log so no logs
        SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 0)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 0)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 0)

    def test_notifications_slacks_and_logs_for_one_contact_preference(self):
        applicant = factories.ApplicantFactory()
        answers = get_answers_for_orgs(
            self.get_orgs(),
            contact_preferences=['prefers_email'],
            email='test@gmail.com',
            phone_number='5554442222',
        )
        sub = factories.FormSubmissionWithOrgsFactory.create(
            applicant=applicant,
            organizations=self.get_orgs(),
            answers=answers)
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 0)
        assertInLogsCount(logs, {'event_name=app_confirmation_sent': 1})


class TestSendToNewappsBundleIfNeeded(TestCase):
    fixtures = [
        'counties',
        'organizations'
    ]

    @patch('intake.tasks.add_application_pdfs')
    def test_calls_task_if_sf_in_sub(self, add_application_pdfs):
        sf_pubdef = Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[sf_pubdef])
        SubmissionsService.send_to_newapps_bundle_if_needed(sub, [sf_pubdef])
        add_application_pdfs.delay.assert_called_with(
            sub.applications.first().id)

    @patch('intake.tasks.add_application_pdfs')
    def test_does_not_call_task_if_not_sf(self, add_application_pdfs):
        a_pubdef = Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[a_pubdef])
        SubmissionsService.send_to_newapps_bundle_if_needed(sub, [a_pubdef])
        add_application_pdfs.delay.assert_not_called()
