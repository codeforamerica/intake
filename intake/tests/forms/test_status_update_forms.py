from django.test import TestCase
from intake import models
from intake.forms import StatusUpdateForm, StatusNotificationForm
from markupsafe import escape


class TestStatusUpdateForm(TestCase):

    fixtures = ['template_options']

    def test_has_expected_fields(self):
        keys = [
            'author', 'application', 'status_type',
            'additional_information', 'next_steps', 'other_next_step']
        form = StatusUpdateForm()
        self.assertEquals(keys, list(form.fields.keys()))

    def test_inactive_next_steps_arent_shown(self):
        next_step = models.NextStep.objects.last()
        next_step.is_active = False
        next_step.save()
        form = StatusUpdateForm()
        rendered_form = form.as_p()
        self.assertNotIn(
            escape(next_step.label),
            rendered_form
        )


class TestStatusNotificationForm(TestCase):

    def test_has_expected_fields(self):
        keys = ['sent_message']
        form = StatusNotificationForm()
        self.assertEquals(keys, list(form.fields.keys()))
