from django.test import TestCase

from django.conf import settings

class TestConfig(TestCase):

    def test_jinja_config(self):
        from project.jinja2 import jinja_config
        env = jinja_config()
        self.assertEqual(env, jinja_config.env)