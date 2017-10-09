from unittest.mock import Mock
from django.test import TestCase

from formation.display_form_base import DisplayForm
from formation.field_types import IntegerField


class NumberField(IntegerField):
    context_key = 'number'


class ExampleDisplayForm(DisplayForm):
    fields = [NumberField]


class TestDisplayForm(TestCase):

    def test_sets_self_and_fields_as_dislay_only(self):
        form = ExampleDisplayForm(dict(number=25))
        self.assertTrue(form.display_only)
        self.assertTrue(form.number.display_only)

    def test_defaults_to_parse_only(self):
        form = ExampleDisplayForm(dict(number=25))
        self.assertTrue(form.skip_validation_parse_only)
        self.assertTrue(form.number.skip_validation_parse_only)
