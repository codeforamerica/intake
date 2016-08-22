from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock


class TestContextProcessors(TestCase):

    def test_oxford_comma(self):
        from project.jinja2 import oxford_comma
        items = ["apples", "oranges", "bananas"]
        expected_phrases = [
            "apples, oranges, and bananas",
            "apples and oranges",
            "apples",
        ]
        for phrase in expected_phrases:
            self.assertEqual(
                phrase, oxford_comma(items))
            items.pop()
