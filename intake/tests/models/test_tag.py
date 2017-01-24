from django.test import TestCase
from intake.tests import mock
from user_accounts.tests.mock import create_user
from taggit.models import Tag
from django.contrib.auth.models import User
from intake import models


class TestSubmissionTagLink(TestCase):

    def setUp(self):
        super().setUp()
        self.sub = mock.make_submission()
        self.sub_id = self.sub.id
        self.user = create_user()
        self.user_id = self.user.id
        self.tag = mock.make_tag()
        self.tag_id = self.tag.id

    def make_link(self):
        link = models.SubmissionTagLink(
            content_object_id=self.sub_id, user_id=self.user_id,
            tag_id=self.tag_id)
        link.save()
        return link

    def test_creation(self):
        link = self.make_link()
        self.assertTrue(link.added)

    def test_related_queries(self):
        link = self.make_link()
        results = self.sub.tags.all()
        self.assertIn(self.tag, results)
        self.assertIn(link, self.tag.intake_submissiontaglink_items.all())
        self.assertIn(link, self.sub.tag_links.all())
        results = models.FormSubmission.objects.filter(
            tags__name=self.tag.name)
        self.assertIn(self.sub, results)

    def test_deletion(self):
        link = self.make_link()
        # make sure related objects still exist after deletion
        link.delete()
        self.assertEqual(
            models.FormSubmission.objects.filter(id=self.sub_id).count(), 1)
        self.assertEqual(
            Tag.objects.filter(id=self.tag_id).count(), 1)
        self.assertEqual(
            User.objects.filter(id=self.user_id).count(), 1)
        self.assertEqual(self.sub.tags.all().count(), 0)

    def test_tag_deletion(self):
        # Deletes link if tag is deleted
        link_id = self.make_link().id
        Tag.objects.filter(id=self.tag_id).delete()
        self.assertEqual(
            models.SubmissionTagLink.objects.filter(id=link_id).count(), 0)

    def test_user_deletion(self):
        # Link remains if user is deleted, with link.user = None
        link_id = self.make_link().id
        User.objects.filter(id=self.user_id).delete()
        link = models.SubmissionTagLink.objects.get(id=link_id)
        self.assertEqual(link.user, None)
