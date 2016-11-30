from django.test import TestCase
from intake import models
from intake import serializers


class TestApplicantSerializer(TestCase):

    fixtures = [
        'counties',
        'organizations',
        'mock_2_submissions_to_cc_pubdef'
    ]

    def test_gets_expected_json(self):
        # applicant with some events
        applicant = models.Applicant.objects.first()
        event = models.ApplicationEvent(
            applicant=applicant,
            name=models.ApplicationEvent.APPLICATION_STARTED,
            data={
                'referrer': 'google.com',
                'ip': '127.0.0.1',
            })
        event.save()

        data = serializers.ApplicantSerializer(applicant).data
        top_keys = [
            'id', 'events',
            'started', 'finished', 'had_errors',
            'ip', 'referrer', 'events',
            'tried_to_apply', 'is_multicounty'
            ]
        event_keys = ['time', 'name', 'data']
        for key in top_keys:
            self.assertIn(key, data)
        for key in event_keys:
            self.assertIn(key, data['events'][0])

    def test_works_without_data(self):
        applicant = models.Applicant.objects.first()
        submission = models.FormSubmission.objects.filter(
            applicant=applicant).first()
        submission.applicant = None
        submission.save()
        data = serializers.ApplicantSerializer(applicant).data
        self.assertTrue(data)


class TestFormSubmissionSerializer(TestCase):

    fixtures = [
        'counties', 'organizations',
        'mock_2_submissions_to_cc_pubdef'
    ]

    def test_doesnt_include_too_much_information(self):

        should_have = [
            'id',
            'contact_preferences',
            'monthly_income',
            'us_citizen',
            'being_charged',
            'serving_sentence',
            'on_probation_parole',
            'currently_employed',
            'city',
            'url',
            'age',
        ]
        shouldnt_have = [
            'first_name',
            'last_name',
            'middle_name',
            'dob',
            'ssn',
            'phone_number',
            'alternate_phone_number',
            'email',
        ]
        submission = models.FormSubmission.objects.all().first()
        data = serializers.FormSubmissionSerializer(submission).data
        for key in should_have:
            self.assertIn(key, data)
        for key in shouldnt_have:
            self.assertNotIn(key, data)
