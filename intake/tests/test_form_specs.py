from unittest import TestCase as BaseTestCase
from django.test import TestCase
from django.contrib.auth.models import User
from formation.forms import (
    county_form_selector, SelectCountyForm, DeclarationLetterFormSpec)

from intake.tests import mock
from intake import models

import intake.services.submissions as SubmissionsService
import intake.services.display_form_service as DisplayFormService


class TestAlamedaCountyForm(TestCase):

    fixtures = ['counties', 'organizations', 'groups', 'mock_profiles']

    def test_records_all_fields(self):
        data = mock.fake.alameda_county_form_answers()
        alameda = models.County.objects.get(slug='alameda')
        Form = county_form_selector.get_combined_form_class(
            counties=[alameda.slug])
        input_form = Form(data)
        self.assertTrue(input_form.is_valid())
        submission = SubmissionsService.create_for_counties(
            counties=[alameda], answers=input_form.cleaned_data)
        output_form = Form(submission.answers)
        self.assertTrue(output_form.is_valid())
        for key in data:
            field = output_form.get_field_by_input_name(key)
            self.assertFalse(
                field.is_empty(), "couldn't find" + field.context_key)

    def test_displays_all_fields(self):
        data = mock.fake.alameda_pubdef_answers()
        alameda = models.County.objects.get(slug='alameda')
        Form = county_form_selector.get_combined_form_class(
            counties=[alameda.slug])
        input_form = Form(data)
        input_form.is_valid()
        submission = SubmissionsService.create_for_counties(
            counties=[alameda], answers=input_form.cleaned_data)
        user = User.objects.get(username="a_pubdef_user")
        display_form, letter_display = \
            DisplayFormService.get_display_form_for_user_and_submission(
                user, submission)
        page_data = str(display_form) + str(letter_display)
        for key in data:
            field = display_form.get_field_by_input_name(key)
            self.assertIn(
                field.get_html_class_name(), page_data,
                "couldn't find " + field.get_html_class_name())


class TestDeclarationLetterForm(TestCase):

    base_form = DeclarationLetterFormSpec().build_form_class()

    def test_records_all_fields(self):
        data = mock.fake.declaration_letter_answers()
        input_form = self.base_form(data)
        self.assertTrue(input_form.is_valid())
        submission = models.FormSubmission(answers=input_form.cleaned_data)
        submission.save()
        output_form = self.base_form(submission.answers)
        self.assertTrue(output_form.is_valid())
        for key in data:
            field = output_form.get_field_by_input_name(key)
            self.assertFalse(
                field.is_empty(), "couldn't find" + field.context_key)

    def test_displays_all_fields(self):
        data = mock.fake.declaration_letter_answers()
        input_form = self.base_form(data)
        self.assertTrue(input_form.is_valid())
        submission = models.FormSubmission(answers=input_form.cleaned_data)
        submission.save()
        output_form = self.base_form(submission.answers)
        self.assertTrue(output_form.is_valid())
        page_data = output_form.display()
        for key in data:
            field = output_form.get_field_by_input_name(key)
            self.assertIn(
                field.get_html_class_name(), page_data,
                "couldn't find " + field.get_html_class_name())


class TestSelectCountyForm(BaseTestCase):

    def test_returns_errors_for_empty_field(self):
        data = {}
        form = SelectCountyForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.counties.is_empty())
        self.assertTrue(form.errors)
        form = SelectCountyForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.counties.is_empty())
        self.assertTrue(form.errors)
