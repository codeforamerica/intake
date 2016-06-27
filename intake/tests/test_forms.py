from django.test import TestCase

from intake import forms
from intake.tests import mock

class TestForms(TestCase):

    def test_application_form_with_mock_answers(self):
        """Should work with a set of mock answers
        """
        fake_answers = mock.fake.sf_county_form_answers()
        form = forms.BaseApplicationForm(fake_answers)
        self.assertTrue(form.is_valid())

    def test_application_form_with_raw_empty_post_data(self):
        """Should not have trouble reading raw post data from
            a Django request.
        """
        form = forms.BaseApplicationForm(mock.RAW_FORM_DATA)
        self.assertTrue(not form.is_valid())

    def test_name_is_minimal_requirement(self):
        """Should be valid with nothing but a name
            Should not be valid with any empty name inputs
        """
        # valid with name only
        form = forms.BaseApplicationForm(
            dict(first_name="Foo", last_name="Bar"))
        self.assertTrue(form.is_valid())

        # invalid if missing either last or first name
        form = forms.BaseApplicationForm(
            dict(first_name=" ", last_name="Bar"))
        self.assertTrue(not form.is_valid())

        form = forms.BaseApplicationForm(
            dict(firt_name="Foo", last_name=" "))
        self.assertTrue(not form.is_valid())

    def test_gives_warning_for_missing_ssn(self):
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['ssn'] = ' '
        form = forms.BaseApplicationForm(fake_answers)
        if form.is_valid():
            warnings = form.get_warnings()
            self.assertIn('ssn', warnings)
            self.assertListEqual(warnings['ssn'], 
                ['The public defender may not be able to check your RAP sheet without a social security number'])

    def test_gives_warning_for_missing_dob(self):
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['dob_day'] = ' '
        form = forms.BaseApplicationForm(fake_answers)
        if form.is_valid():
            warnings = form.get_warnings()
            self.assertIn('dob', warnings)
            self.assertListEqual(warnings['dob'], 
                ['The public defender may not be able to check your RAP sheet without a full date of birth'])

    def test_gives_warning_for_missing_address(self):
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['address_street'] = ' '
        form = forms.BaseApplicationForm(fake_answers)
        if form.is_valid():
            warnings = form.get_warnings()
            self.assertIn('address', warnings)
            self.assertListEqual(warnings['address'], 
                ['The public defender needs a mailing address to send you a letter with the next steps'])


