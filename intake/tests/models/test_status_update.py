from django.test import TestCase
from intake import models

from intake.tests.mock import *


class TestStatusUpdate(TestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef'
        ]

    def test_cannot_be_built_without_application(self):
        self.assertEqual("xyz", "abc")

    def test_has_default_values(self):
        # timestamps
        self.assertEqual("xyz", "abc")

    def test_cannot_be_built_without_author(self):
        self.assertEqual("xyz", "abc")

    def test_cannot_be_built_without_status(self):
        self.assertEqual("xyz", "abc")

    def test_can_be_built_without_next_steps(self):
        self.assertEqual("xyz", "abc")
