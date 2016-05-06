from django.test import TestCase
from datetime import datetime

from tests.factories import FormSubmissionFactory
from intake.models import FormSubmission

class TestModels(TestCase):

    def test_submission(self):
        submission = FormSubmissionFactory()
        self.assertEqual(int, type(submission.id))
        self.assertEqual(datetime, type(submission.date_received))
        self.assertEqual(dict, type(submission.answers))
        self.assertEqual(
            FormSubmission.objects.get(id=submission.id), submission)
