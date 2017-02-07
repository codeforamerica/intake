from django.test import TestCase
from intake.forms import StatusUpdateForm, StatusNotificationForm


class TestStatusUpdateForm(TestCase):
    def test_has_expected_fields(self):
        keys = [
            'author', 'application', 'status_type',
            'additional_information', 'next_steps', 'other_next_step']
        form = StatusUpdateForm()
        self.assertEquals(keys, list(form.fields.keys()))

    def test_non_live_next_steps_arent_shown(self):
        raise NotImplementedError


class TestStatusNotificationForm(TestCase):
    def test_has_expected_fields(self):
        keys = ['sent_message']
        form = StatusNotificationForm()
        self.assertEquals(keys, list(form.fields.keys()))
