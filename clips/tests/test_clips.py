from django.test import TestCase
from clips.models import Clip, run_query
from clips.tests.factories.clip_factory import ClipFactory


class TestClips(TestCase):

    def test_run_query(self):
        """Test that it can run a query on the database
        without erroring
        """

        result = run_query("select id from auth_user")
        self.assertEquals(result, [['id']])

    def test_clip_all(self):
        """Test that get_all returns undeleted Clips by default"""
        clip_one = ClipFactory(title='Query one')
        clip_two = ClipFactory()
        clip_two.delete()

        self.assertEquals(len(Clip.objects.all()), 1)
        self.assertEquals(Clip.objects.all()[0], clip_one)
