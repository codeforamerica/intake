from unittest.mock import Mock
from django.test import TestCase

from intake.tests import mock
from formation import field_types
import intake.services.submissions as SubmissionsService
from user_accounts import models as auth_models
from intake import (
    models,
    constants)


class TestFormSubmission(TestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_1_submission_to_multiple_orgs']

    def get_a_sample_sub(self):
        return models.FormSubmission.objects.filter(
            organizations__slug='a_pubdef').first()

    def test_get_counties(self):
        organizations = auth_models.Organization.objects.all()
        # a submission for all organizations
        submission = SubmissionsService.create_for_organizations(
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
        result = SubmissionsService.get_permitted_submissions(mock_user)
        self.assertListEqual(list(result), list(subs))

    def test_get_permitted_submisstions_when_not_permitted(self):
        cc_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.COCO_PUBDEF)
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        submission = SubmissionsService.create_for_organizations(
            [cc_pubdef], answers={})
        mock_user = Mock(is_staff=False, **{'profile.organization': sf_pubdef})
        result = SubmissionsService.get_permitted_submissions(
            mock_user, [submission.id])
        self.assertListEqual(list(result), [])

    def test_get_permitted_submissions_when_staff(self):
        orgs = auth_models.Organization.objects.all()
        for org in orgs:
            SubmissionsService.create_for_organizations([org], answers={})
        subs = set(models.FormSubmission.objects.all())
        mock_user = Mock(is_staff=True)
        result = SubmissionsService.get_permitted_submissions(mock_user)
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
