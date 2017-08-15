from django.test import TestCase
from clips.models import Clip, run_query


class TestModels(TestCase):

    def test_run_query(self):
        result = run_query("select * from auth_user")
        self.assertEquals(result, [[]])
