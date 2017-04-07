from django.test import TestCase
from intake import models
from intake import serializers


class TestApplicantSerializer(TestCase):

    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
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
