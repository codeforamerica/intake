from django.test import TestCase
from clips.models import Clip, run_query


class TestClips(TestCase):

    def test_run_query(self):
        """Test that it can run a query on the database
        without erroring
        """

        result = run_query("select id from auth_user")
        self.assertEquals(result, [['id']])
