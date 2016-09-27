from django.test import TestCase
from intake import models
from intake import serializers


class TestApplicantSerializer(TestCase):

    fixtures = [
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
                'referrer': 'google.com'
            })
        event.save()

        data = serializers.ApplicantSerializer(applicant).data
        top_keys = ['id', 'events', 'form_submissions']
        event_keys = ['id', 'name', 'data']
        submission_keys = ['id', 'answers']
        for key in top_keys:
            self.assertIn(key, data)
        for key in event_keys:
            self.assertIn(key, data['events'][0])
        for key in submission_keys:
            self.assertIn(key, data['form_submissions'][0])
