from django.test import TestCase

import intake.services.submissions as SubmissionsService
from user_accounts import models as auth_models
from intake.tests import mock
from intake import models, constants


class TestApplicationLogEntry(TestCase):
    fixtures = [
        'counties',
        'organizations',
        'mock_profiles',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
        ]

    def test_can_log_referral_between_orgs(self):
        from_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.ALAMEDA_PUBDEF)
        to_org = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        from_org_user = from_org.profiles.first().user
        answers = mock.fake.alameda_pubdef_answers()
        submission = SubmissionsService.create_for_organizations(
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
