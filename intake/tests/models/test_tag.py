from django.test import TestCase
from intake.tests.factories import SubmissionTagLinkFactory
from intake import models
from taggit.models import Tag
from django.contrib.auth.models import User


class TestSubmissionTagLink(TestCase):

    def test_creation(self):
        link = SubmissionTagLinkFactory()
        self.assertTrue(link.added)

    def test_related_queries(self):
        link = SubmissionTagLinkFactory()
        results = link.content_object.tags.all()
        self.assertIn(link.tag, results)
        self.assertIn(link, link.tag.intake_submissiontaglink_items.all())
        self.assertIn(link, link.content_object.tag_links.all())
        results = models.FormSubmission.objects.filter(
            tags__name=link.tag.name)
        self.assertIn(link.content_object, results)

    def test_deletion(self):
        link = SubmissionTagLinkFactory()
        # make sure related objects still exist after deletion
        link.delete()
        self.assertEqual(
            models.FormSubmission.objects.filter(
                id=link.content_object_id).count(), 1)
        self.assertEqual(
            Tag.objects.filter(id=link.tag_id).count(), 1)
        self.assertEqual(
            User.objects.filter(id=link.user_id).count(), 1)
        self.assertEqual(link.content_object.tags.all().count(), 0)

    def test_tag_deletion(self):
        # Deletes link if tag is deleted
        link = SubmissionTagLinkFactory()
        Tag.objects.filter(id=link.tag_id).delete()
        self.assertEqual(
            models.SubmissionTagLink.objects.filter(id=link.id).count(), 0)

    def test_user_deletion(self):
        # Link remains if user is deleted, with link.user = None
        link = SubmissionTagLinkFactory()
        User.objects.filter(id=link.user_id).delete()
        link = models.SubmissionTagLink.objects.get(id=link.id)
        self.assertEqual(link.user, None)
