# from copy import deepcopy
# from datetime import timedelta
# from unittest import TestCase
from django.test import TestCase as DjangoTestCase

from intake.tests.mock_serialized_apps import apps as all_apps
from intake import aggregate_serializer_fields as fields


class TestFinishedCountField(DjangoTestCase):

    def test_returns_correct_count(self):
        field = fields.FinishedCountField()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 9)


class TestMeanCompletionTimeField(DjangoTestCase):

    def test_returns_correct_mean(self):
        field = fields.MeanCompletionTimeField()
        result = field.to_representation(all_apps)
        expected = 441.5181111111111
        difference = abs(expected - result)
        self.assertTrue(difference < 0.00001)


class TestMedianCompletionTimeField(DjangoTestCase):

    def test_returns_correct_median(self):
        field = fields.MedianCompletionTimeField()
        result = field.to_representation(all_apps)
        expected = 417.204
        difference = abs(expected - result)
        self.assertTrue(difference < 0.00001)


class TestMajorSourcesField(DjangoTestCase):

    def test_returns_correct_sources(self):
        field = fields.MajorSourcesField()
        result = field.to_representation(all_apps)
        expected = {
            'www.codeforamerica.org',
            'www.google.com',
            'www.safeandjust.org',
            'sfpublicdefender.org',
            'checkrapplicant.zendesk.com'}
        self.assertEqual(set(result.keys()), expected)


class TestDropOffField(DjangoTestCase):

    def test_returns_correct_dropoff(self):
        field = fields.DropOffField()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 1.0)


class TestMultiCountyField(DjangoTestCase):

    def test_returns_correct_multicounty_amount(self):
        field = fields.MultiCountyField()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 0.1111111111111111)
