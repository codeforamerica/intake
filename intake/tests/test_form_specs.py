from django.test import TestCase
from django.contrib.auth.models import User
from formation.forms import county_form_selector

from intake.tests import mock
from intake import constants, models


class TestAlamedaCountyForm(TestCase):

    fixtures = ['organizations', 'mock_profiles']

    def test_records_all_fields(self):
        data = mock.fake.alameda_county_form_answers()
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        Form = county_form_selector.get_combined_form_class(
            counties=[alameda.slug])
        input_form = Form(data)
        self.assertTrue(input_form.is_valid())
        submission = models.FormSubmission.create_for_counties(
            counties=[alameda], answers=input_form.cleaned_data)
        output_form = Form(submission.answers)
        self.assertTrue(output_form.is_valid())
        for key in data:
            field = output_form.get_field_by_input_name(key)
            self.assertFalse(field.is_empty(), field.context_key)

    def test_displays_all_fields(self):
        data = mock.fake.alameda_pubdef_answers()
        alameda = models.County.objects.get(slug=constants.Counties.ALAMEDA)
        Form = county_form_selector.get_combined_form_class(
            counties=[alameda.slug])
        input_form = Form(data)
        input_form.is_valid()
        submission = models.FormSubmission.create_for_counties(
            counties=[alameda], answers=input_form.cleaned_data)
        user = User.objects.get(username="a_pubdef_user")
        display_form = submission.get_display_form_for_user(user)
        page_data = str(display_form)
        for key in data:
            field = display_form.get_field_by_input_name(key)
            self.assertIn(field.get_html_class_name(), page_data,
                "couldn't find " + field.get_html_class_name())


        
