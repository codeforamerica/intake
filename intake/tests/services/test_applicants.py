from django.test import TestCase
import intake.services.applicants as ApplicantServices
from intake.tests import factories, mock_utils


class TestGetApplicantsWithMultipleSubmissions(TestCase):

    def test_expected_success(self):
        applicant = factories.ApplicantFactory()
        for i in range(2):
            factories.FormSubmissionFactory(applicant=applicant)
        results = ApplicantServices.get_applicants_with_multiple_submissions()
        self.assertListEqual(
            list(results),
            [applicant])


class TestCreateNewApplicant(TestCase):

    def test_doesnt_fail_if_visitor_has_applicant(self):
        existing_applicant = factories.ApplicantFactory()
        mock_request = mock_utils.SimpleMock(
            visitor=existing_applicant.visitor, session={})
        applicant = ApplicantServices.create_new_applicant(mock_request)
        self.assertEqual(applicant, existing_applicant)
