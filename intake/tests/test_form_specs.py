from django.test import TestCase
from formation.forms import county_form_selector

from intake.tests import mock
from intake import constants, models


class TestAlamedaCountyForm(TestCase):

    fixtures = ['organizations']

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
            self.assertFalse(field.is_empty())
