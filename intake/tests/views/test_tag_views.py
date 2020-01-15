from intake.tests.base_testcases import APIViewTestCase
from django.urls import reverse
from intake import models
from intake.tests import mock
from user_accounts.tests.mock import create_user


class TestAddTags(APIViewTestCase):

    def assertTagsHaveNames(self, serialized_tags, names):
        tag_names = sorted([tag['name'] for tag in serialized_tags])
        names = sorted(names)
        for name, tag_name in zip(names, tag_names):
            self.assertEqual(name, tag_name)

    def post_tags(self, user, **kwargs):
        sub_id = mock.make_submission().id
        data = dict(
            tags="apple, banana",
            submission=sub_id,
            user=user.id
        )
        data.update(kwargs)
        return self.client.post(reverse('intake-add_tags'), data)

    def test_returns_201_for_valid_input(self):
        user = self.be_cfa_user()
        response = self.post_tags(user)
        self.assertEqual(response.status_code, 201)
        # here we can test the
        serialized_tags = response.json()
        self.assertTagsHaveNames(serialized_tags, ['apple', 'banana'])

    def test_all_nonstaff_get_403(self):
        user = self.be_monitor_user()
        response = self.post_tags(user)
        self.assertEqual(response.status_code, 403)
        user = self.be_apubdef_user()
        response = self.post_tags(user)
        self.assertEqual(response.status_code, 403)
        self.be_anonymous()
        response = self.post_tags(user)
        self.assertEqual(response.status_code, 302)

    def test_returns_errors_for_invalid_input(self):
        user = self.be_cfa_user()
        response = self.post_tags(user, submission="")
        self.assertEqual(response.status_code, 400)


class TestRemoveTag(APIViewTestCase):

    def setUp(self):
        super().setUp()
        self.tag = mock.make_tag("remove me")
        self.sub = mock.make_submission()
        self.user = create_user()
        self.link = models.SubmissionTagLink(
            content_object=self.sub,
            tag=self.tag,
            user=self.user)
        self.link.save()

    def post_remove_tag(self, user):
        # /tags/1/remove/51/
        return self.client.post(
            reverse(
                'intake-remove_tag',
                kwargs=dict(
                    tag_id=self.tag.id,
                    submission_id=self.sub.id))
        )

    def test_returns_204_for_successful_destroy(self):
        user = self.be_cfa_user()
        response = self.post_remove_tag(user)
        self.assertEqual(response.status_code, 204)

    def test_all_nonstaff_get_403(self):
        user = self.be_monitor_user()
        response = self.post_remove_tag(user)
        self.assertEqual(response.status_code, 403)
        user = self.be_apubdef_user()
        response = self.post_remove_tag(user)
        self.assertEqual(response.status_code, 403)
        self.be_anonymous()
        response = self.post_remove_tag(user)
        self.assertEqual(response.status_code, 302)
