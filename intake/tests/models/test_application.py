from django.test import TestCase
from intake import models
from user_accounts import models as user_account_models
from django.db import IntegrityError


class TestApplicant(TestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef'
        ]

    def test_cannot_create_without_organization(self):
        form_submission = models.FormSubmission.objects.first()
        application = models.Application(form_submission=form_submission)
        with self.assertRaises(IntegrityError):
            application.save()

    def test_cannot_create_without_form_submission(self):
        organization = user_account_models.Organization.objects.first()
        application = models.Application(organization=organization)
        with self.assertRaises(IntegrityError):
            application.save()

    def test_can_create_with_org_and_sub(self):
        form_submission = models.FormSubmission.objects.first()
        organization = user_account_models.Organization.objects.get(slug="cfa")
        application = models.Application(
            form_submission=form_submission,
            organization=organization)
        application.save()
        self.assertTrue(application.id)
