from django.test import TestCase

from project.decorators import run_if_setting_true


class TestRunIfSettingTrue(TestCase):

    @run_if_setting_true("MY_SETTING", "foo")
    def sample_function(self):
        return "bar"

    def test_with_setting_undefined(self):
        self.assertEqual(self.sample_function(), "foo")

    def test_with_setting_true(self):
        with self.settings(MY_SETTING=True):
            self.assertEqual(self.sample_function(), "bar")

    def test_with_setting_false(self):
        with self.settings(MY_SETTING=False):
            self.assertEqual(self.sample_function(), "foo")
