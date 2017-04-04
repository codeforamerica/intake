from django.test import TestCase
from intake import models
from intake import serializers


class TestFormSubmissionSerializer(TestCase):

    fixtures = [
        'counties', 'organizations', 'groups', 'mock_profiles',
        'mock_2_submissions_to_cc_pubdef', 'template_options'
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
