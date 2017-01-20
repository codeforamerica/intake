from django.test import TestCase
from intake import models


class TestStatusUpdate(TestCase):

    # set up fixtures here

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
