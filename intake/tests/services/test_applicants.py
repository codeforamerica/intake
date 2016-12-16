from django.test import TestCase
import intake.services.applicants as ApplicantServices
from intake import models
from intake.tests import mock


class TestGetApplicantsWithMultipleSubmissions(TestCase):

    def test_expected_success(self):
        applicant = models.Applicant()
        applicant.save()
        for i in range(2):
            mock.FormSubmissionFactory(applicant=applicant)
        results = ApplicantServices.get_applicants_with_multiple_submissions()
        self.assertListEqual(
            list(results),
            [applicant])
