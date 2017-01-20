from django.test import TestCase
from intake import models


class TestStatusNotification(TestCase):

    def test_slug_must_be_unique(self):
        self.assertEqual("xyz", "abc")

    def test_requires_all_fields_but_help_text_and_addl_info(self):
        # can split out into two with missing help text/addl info
        self.assertEqual("xyz", "abc")

    def test_successful_save_with_all_fields(self):
        self.assertEqual("xyz", "abc")
