from django.test import TestCase
import intake.services.applicants as ApplicantServices
from intake.tests import factories


class TestGetApplicantsWithMultipleSubmissions(TestCase):

    def test_expected_success(self):
        applicant = factories.ApplicantFactory()
        for i in range(2):
            factories.FormSubmissionFactory(applicant=applicant)
        results = ApplicantServices.get_applicants_with_multiple_submissions()
        self.assertListEqual(
            list(results),
            [applicant])
