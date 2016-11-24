from django.test import TestCase as DjangoTestCase

from intake.tests.mock_serialized_apps import apps as all_apps
from intake import aggregate_serializer_fields as fields


class TestFinishedCountField(DjangoTestCase):

    def test_returns_correct_count(self):
        field = fields.FinishedCountField()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 9)

    def test_returns_zero_for_empty_list(self):
        field = fields.FinishedCountField()
        result = field.to_representation([])
        self.assertEqual(result, 0)


class TestMeanCompletionTimeField(DjangoTestCase):

    def test_returns_correct_mean(self):
        field = fields.MeanCompletionTimeField()
        result = field.to_representation(all_apps)
        expected = 441.5181111111111
        difference = abs(expected - result)
        self.assertTrue(difference < 0.00001)

    def test_returns_none_for_empty_list(self):
        field = fields.MeanCompletionTimeField()
        result = field.to_representation([])
        self.assertIsNone(result)


class TestMedianCompletionTimeField(DjangoTestCase):

    def test_returns_correct_median(self):
        field = fields.MedianCompletionTimeField()
        result = field.to_representation(all_apps)
        expected = 417.204
        difference = abs(expected - result)
        self.assertTrue(difference < 0.00001)

    def test_returns_none_for_empty_list(self):
        field = fields.MedianCompletionTimeField()
        result = field.to_representation([])
        self.assertIsNone(result)


class TestDropOff(DjangoTestCase):

    def test_returns_correct_dropoff(self):
        field = fields.DropOff()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 0.0)

    def test_returns_zero_for_empty_list(self):
        field = fields.DropOff()
        result = field.to_representation([])
        self.assertEqual(result, 0)


class TestMultiCountyField(DjangoTestCase):

    def test_returns_correct_multicounty_amount(self):
        field = fields.MultiCountyField()
        result = field.to_representation(all_apps)
        self.assertEqual(result, 0.1111111111111111)

    def test_returns_none_for_empty_list(self):
        field = fields.MultiCountyField()
        result = field.to_representation([])
        self.assertIsNone(result)


class TestChannels(DjangoTestCase):

    def test_returns_empty_list_if_no_apps(self):
        field = fields.Channels()
        result = field.to_representation([])
        self.assertEqual(result, [])
