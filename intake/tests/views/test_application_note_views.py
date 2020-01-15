import logging
from intake.tests.base_testcases import APIViewTestCase
from django.urls import reverse
from intake.tests import mock
from project.tests.assertions import assertInLogsCount


class TestCreateNote(APIViewTestCase):

    def post_new_note(self, user, **kwargs):
        sub_id = mock.make_submission().id
        data = dict(
            body="Coffee might help",
            submission=sub_id,
            user=user.id
        )
        data.update(kwargs)
        return self.client.post(reverse('intake-create_note'), data)

    def test_returns_201_for_valid_input(self):
        user = self.be_cfa_user()
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.post_new_note(user)
        self.assertEqual(response.status_code, 201)
        # here we can test the
        serialized_note = response.json()
        self.assertEqual(
            serialized_note['body'], "Coffee might help")
        for expected_key in ['submission', 'user', 'created', 'id']:
            self.assertIn(expected_key, serialized_note)
            self.assertTrue(serialized_note[expected_key])
        assertInLogsCount(logs, {'event_name=app_note_added': 1})

    def test_all_nonstaff_get_403(self):
        user = self.be_monitor_user()
        response = self.post_new_note(user)
        self.assertEqual(response.status_code, 403)
        user = self.be_apubdef_user()
        response = self.post_new_note(user)
        self.assertEqual(response.status_code, 403)
        self.be_anonymous()
        response = self.post_new_note(user)
        self.assertEqual(response.status_code, 302)

    def test_returns_errors_for_invalid_input(self):
        user = self.be_cfa_user()
        response = self.post_new_note(user, body="")
        self.assertEqual(response.status_code, 400)
        errors = response.json()['body']
        self.assertIn('This field may not be blank.', errors)


class TestDestroyNote(APIViewTestCase):

    def post_note_destruction(self, user):
        sub_id = mock.make_submission().id
        note = mock.make_note(user, sub_id)
        return self.client.post(
            reverse(
                'intake-destroy_note',
                kwargs=dict(pk=note.id))
        )

    def test_returns_204_for_successful_destroy(self):
        user = self.be_cfa_user()
        response = self.post_note_destruction(user)
        self.assertEqual(response.status_code, 204)

    def test_all_nonstaff_get_403(self):
        user = self.be_monitor_user()
        response = self.post_note_destruction(user)
        self.assertEqual(response.status_code, 403)
        user = self.be_apubdef_user()
        response = self.post_note_destruction(user)
        self.assertEqual(response.status_code, 403)
        self.be_anonymous()
        response = self.post_note_destruction(user)
        self.assertEqual(response.status_code, 302)
