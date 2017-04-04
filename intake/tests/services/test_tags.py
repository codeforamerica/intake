from django.test import TestCase
from intake.tests.base_testcases import IntakeDataTestCase
from intake.tests import mock
from user_accounts.tests.mock import create_user
from intake.models import SubmissionTagLink
import intake.services.tags as TagsService
from intake.exceptions import UserCannotBeNoneError


class TestUpdateTagsForSubmission(IntakeDataTestCase):

    fixtures = [
        'counties', 'organizations', 'groups', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef', 'template_options'
    ]

    def setUp(self):
        super().setUp()
        # two tags, one unlinked
        mock.make_tag("old")
        existing = mock.make_tag("existing")
        self.sub = self.submissions[0]
        self.user = self.cfa_user
        link = SubmissionTagLink(
            user=self.user, content_object=self.sub, tag=existing)
        link.save()

    def assertTagsHaveNames(self, serialized_tags, names):
        tag_names = sorted([tag['name'] for tag in serialized_tags])
        names = sorted(names)
        for name, tag_name in zip(names, tag_names):
            self.assertEqual(name, tag_name)

    def test_all_new_tags(self):
        result = TagsService.update_tags_for_submission(
            self.cfa_user.id, self.sub.id, "new, thing")
        self.assertTagsHaveNames(result, ["existing", "new", "thing"])

    def test_some_new_tags(self):
        result = TagsService.update_tags_for_submission(
            self.cfa_user.id, self.sub.id, "old, new")
        self.assertTagsHaveNames(result, ["existing", "new", "old"])

    def test_no_new_tags(self):
        result = TagsService.update_tags_for_submission(
            self.cfa_user.id, self.sub.id, "old, existing")
        self.assertTagsHaveNames(result, ["existing", "old"])

    def test_same_tags_as_existing(self):
        result = TagsService.update_tags_for_submission(
            self.cfa_user.id, self.sub.id, "existing")
        self.assertTagsHaveNames(result, ["existing"])

    def test_bad_user(self):
        with self.assertRaises(UserCannotBeNoneError):
            TagsService.update_tags_for_submission(
                None, self.sub.id, "existing")

    def test_bad_submission(self):
        with self.assertRaises(ValueError):
            TagsService.update_tags_for_submission(
                self.cfa_user.id, None, "existing")

    def test_empty_tags(self):
        result = TagsService.update_tags_for_submission(
            self.cfa_user.id, self.sub.id, ", ,")
        self.assertTagsHaveNames(result, ["existing"])


class TestGetAllUsedTagNames(TestCase):

    def test_doesnt_return_unused_tags(self):
        mock.make_tag()
        results = TagsService.get_all_used_tag_names()
        self.assertEqual(list(results), [])

    def test_returns_used_tags(self):
        tag = mock.make_tag("example")
        sub = mock.make_submission()
        user = create_user()
        link = SubmissionTagLink(
            user=user, content_object=sub, tag=tag)
        link.save()
        results = TagsService.get_all_used_tag_names()
        self.assertEqual(list(results), ["example"])


class TestRemoveTagFromSubmission(TestCase):

    def setUp(self):
        super().setUp()
        self.tag = mock.make_tag()
        self.sub = mock.make_submission()
        self.user = create_user()
        link = SubmissionTagLink(
            user=self.user, content_object=self.sub, tag=self.tag)
        link.save()

    def test_success(self):
        TagsService.remove_tag_from_submission(self.tag.id, self.sub.id)
        self.assertEqual(SubmissionTagLink.objects.all().count(), 0)

    def test_bad_submission(self):
        count, details = TagsService.remove_tag_from_submission(
            self.tag.id, None)
        self.assertEqual(count, 0)

    def test_bad_tag(self):
        count, details = TagsService.remove_tag_from_submission(
            None, self.sub.id)
        self.assertEqual(count, 0)
