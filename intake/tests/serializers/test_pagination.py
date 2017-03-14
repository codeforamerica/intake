from django.test import TestCase
from collections import OrderedDict
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES
from intake import models, serializers
from django.core.paginator import Paginator


class TestGetPaginatedSerializerClass(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_works_as_expected(self):
        # have a queryset of applications and a serializer
        queryset = models.FormSubmission.objects.all()
        serializer = serializers.FormSubmissionSerializer
        # paginate them
        page = Paginator(queryset, 2).page(2)
        serialized_page = serializers.serialize_page(page, serializer)
        for thing in serialized_page:
            self.assertTrue(isinstance(thing, OrderedDict))
            self.assertEqual(
                [key for key in thing.keys()],
                ['id', 'date_received', 'organizations',
                 'contact_preferences', 'monthly_income', 'us_citizen',
                 'being_charged', 'serving_sentence', 'on_probation_parole',
                 'currently_employed', 'city', 'age', 'url',
                 'where_they_heard'])
        self.assertEqual(serialized_page.number, 2)
        self.assertEqual(serialized_page.has_next(), True)
        self.assertEqual(serialized_page.has_previous(), True)
        self.assertEqual(serialized_page.has_other_pages(), True)
