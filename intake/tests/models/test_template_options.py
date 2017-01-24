from django.test import TestCase
from intake import models
from intake.tests.factories import StatusTypeFactory
from django.db import IntegrityError


class TestTemplateOption(TestCase):

    def test_slug_must_be_unique(self):
        existing_status_type = StatusTypeFactory.create()
        new_status_type = StatusTypeFactory.build()
        with self.assertRaises(IntegrityError):
            new_status_type.save()
