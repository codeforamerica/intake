from django.test import TestCase
from collections import OrderedDict
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES
from intake import models, serializers, services


class TestGetPaginatedSerializerClass(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_works_as_expected(self):
        # have a queryset of applications and a serializer
        queryset = models.FormSubmission.objects.all()
        serializer = serializers.FormSubmissionFollowupListSerializer
        results = services.pagination.get_serialized_page(
            queryset, serializer, page_index=2, max_count_per_page=2)
        for thing in results:
            self.assertTrue(isinstance(thing, OrderedDict))
            self.assertEqual(
                [key for key in thing.keys()],
                ['id', 'local_date_received', 'full_name', 'url',
                 'phone_number', 'email', 'applications', 'notes', 'tags'])
        self.assertEqual(results.number, 2)
        self.assertEqual(results.has_next(), True)
        self.assertEqual(results.has_previous(), True)
        self.assertEqual(results.has_other_pages(), True)
