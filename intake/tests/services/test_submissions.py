from unittest.mock import Mock, patch
from django.test import TestCase
from django.db.models import Count
import intake.services.submissions as SubmissionsService
from intake.tests import mock, factories
from intake.tests.mock_org_answers import get_answers_for_orgs
from intake.tests.base_testcases import (
    ExternalNotificationsPatchTestCase, ALL_APPLICATION_FIXTURES)
from formation.forms import county_form_selector
from intake.constants import (
    COUNTY_CHOICE_DISPLAY_DICT, Organizations,
    EMAIL, SMS)
from intake.models import (
    ApplicationEvent, FormSubmission, ApplicationLogEntry)
from intake import constants, models
from user_accounts.models import Organization, UserProfile

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
        # assert that the correct event was created
        events = ApplicationEvent.objects.filter(
            applicant_id=applicant.id).all()
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0].name, ApplicationEvent.APPLICATION_SUBMITTED)
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
        SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 1)
        self.assertEqual(
            applicant.events.filter(
                name=ApplicationEvent.CONFIRMATION_SENT).count(), 2)

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
        SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 0)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 0)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 0)
        self.assertEqual(
            applicant.events.filter(
                name=ApplicationEvent.CONFIRMATION_SENT).count(), 0)

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
        SubmissionsService.send_confirmation_notifications(sub)
        self.assertEqual(
            len(self.notifications.slack_notification_sent.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.email_confirmation.send.mock_calls), 1)
        self.assertEqual(
            len(self.notifications.sms_confirmation.send.mock_calls), 0)
        self.assertEqual(
            applicant.events.filter(
                name=ApplicationEvent.CONFIRMATION_SENT).count(), 1)


class TestGetUnopenedSubmissionsForOrg(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_uses_only_one_query(self):
        org = Organization.objects.filter(
            is_receiving_agency=True).first()
        subs = SubmissionsService.get_unopened_submissions_for_org(org)
        with self.assertNumQueries(1):
            list(subs)

    def test_returns_all_apps_if_no_open_events(self):
        ebclc = Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        for org in Organization.objects.filter(
                is_receiving_agency=True):
            subs = SubmissionsService.get_unopened_submissions_for_org(org)
            if org == ebclc:
                self.assertEqual(subs.count(), 2)
            else:
                self.assertEqual(subs.count(), 3)

    def test_returns_apps_opened_by_other_org(self):
        # assume we have a multi-org app opened by a user from one org
        cc_pubdef = Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        a_pubdef = Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        cc_pubdef_user = UserProfile.objects.filter(
            organization=cc_pubdef).first().user
        sub = FormSubmission.objects.annotate(
            org_count=Count('organizations')).filter(org_count__gte=3).first()
        ApplicationLogEntry.log_opened([sub.id], cc_pubdef_user)
        # assert that it shows up in unopened apps
        cc_pubdef_subs = \
            SubmissionsService.get_unopened_submissions_for_org(cc_pubdef)
        a_pubdef_subs = \
            SubmissionsService.get_unopened_submissions_for_org(a_pubdef)
        self.assertIn(sub, a_pubdef_subs)
        self.assertNotIn(sub, cc_pubdef_subs)

    @patch('intake.models.ApplicationEvent.from_logs')
    def test_deleted_opened_app_doesnt_inhibit_return_of_other_apps(
            self, from_logs):
        # https://code.djangoproject.com/ticket/25467?cversion=0&cnum_hist=2
        sf_pubdef = Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        sf_pubdef_user = UserProfile.objects.filter(
            organization=sf_pubdef).first().user
        logs = ApplicationLogEntry.log_opened([None], user=sf_pubdef_user)
        self.assertTrue(logs[0].id)
        self.assertIsNone(logs[0].submission_id)
        unopened_subs = \
            SubmissionsService.get_unopened_submissions_for_org(sf_pubdef)
        self.assertEqual(unopened_subs.count(), 3)
