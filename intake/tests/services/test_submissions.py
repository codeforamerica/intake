from django.test import TestCase

import intake.services.submissions as SubmissionsService
from intake.tests import mock
from formation.forms import county_form_selector
from intake.constants import COUNTY_CHOICE_DISPLAY_DICT, Organizations
from intake.models import Applicant, ApplicationEvent
from user_accounts.models import Organization

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
        applicant = Applicant()
        applicant.save()
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


class TestGetPermittedSubmissions(TestCase):

    fixtures = [
        'counties', 'organizations',
        'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_cc_pubdef',
    ]

    def test_filters_to_organization_of_user(self):
        """Given a user from one org who tries to access all submissions
        assert that they only receive submissions for their org
        """
        # given a user from one org
        org = Organization.objects.get(slug=Organizations.ALAMEDA_PUBDEF)
        user = org.profiles.first().user
        # who requests all submissions
        submissions = SubmissionsService.get_permitted_submissions(user)
        # make sure they only receive those subs targeted to their org
        for sub in submissions:
            orgs = list(sub.organizations.all())
            self.assertIn(org, orgs)
