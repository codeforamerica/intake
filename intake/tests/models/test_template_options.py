from django.test import TestCase
from intake import models
from intake.validators import template_field_renders_correctly
from intake.tests.factories import StatusTypeFactory
from django.db import IntegrityError
from django.core.exceptions import ValidationError


class TestTemplateOption(TestCase):

    fixtures = ['counties', 'organizations', 'template_options']

    def test_slug_must_be_unique(self):
        # create a status type
        StatusTypeFactory.create()
        new_status_type = StatusTypeFactory.build()
        # try to save another with the same slug
        with self.assertRaises(IntegrityError):
            new_status_type.save()

    def test_all_template_fixtures_have_valid_templates(self):
        templates = list(
            models.NextStep.objects.all().values_list('template', flat=True))
        templates.extend(list(
            models.NextStep.objects.all().values_list('template', flat=True)))
        validation_errors = []
        for template in templates:
            try:
                template_field_renders_correctly(template)
            except ValidationError as error:
                validation_errors.append(error)
        self.assertListEqual([], validation_errors)
