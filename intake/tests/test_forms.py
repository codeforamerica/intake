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
            self.assertListEqual(warnings['ssn'], [forms.Warnings.SSN])

    def test_gives_warning_for_missing_dob(self):
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['dob_day'] = ' '
        form = forms.BaseApplicationForm(fake_answers)
        if form.is_valid():
            warnings = form.get_warnings()
            self.assertIn('dob', warnings)
            self.assertListEqual(warnings['dob'], [forms.Warnings.DOB])

    def test_gives_warning_for_missing_address(self):
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['address_street'] = ' '
        form = forms.BaseApplicationForm(fake_answers)
        if form.is_valid():
            warnings = form.get_warnings()
            self.assertIn('address', warnings)
            self.assertListEqual(warnings['address'], [forms.Warnings.ADDRESS])

    def test_form_render_is_equivalent_to_previous_form(self):
        from django.template import loader
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['contact_preferences'] = ['prefers_email', 'prefers_sms']
        form = forms.BaseApplicationForm(fake_answers)
        context = {'form': form}

        # previous = loader.get_template('application_form.jinja').render(context)
        new = loader.get_template('apply_page.jinja').render(context)
        # open("tests/new.html", "w").write(new)
        # open("tests/previous.html", "w").write(previous)
        # self.assertHTMLEqual(
        #     previous, new
        #     )

    def test_check_options_macro(self):
        from django.template import loader
        jinja = loader.engines['jinja']
        template = jinja.env.from_string("""{% import 'macros.jinja' as macros -%}
        {{- macros.checkbox_options_field(form.contact_preferences) -}}
        """)
        fake_answers = mock.fake.sf_county_form_answers()
        fake_answers['contact_preferences'] = ['prefers_email', 'prefers_sms']
        form = forms.BaseApplicationForm(fake_answers)
        context = {'form': form}
        results = template.render(context)
        expected = """
    <div class="field field-checkbox_options contact_preferences">
        <legend>
            How would you like us to contact you?
        </legend>
        <div class="field-help_text">
            Code for America will use this to update you about your application.
        </div>
        <ul class="checkbox_options options_list">
        <li>
            <label class="field-option_label">
                <input type="checkbox" name="contact_preferences" value="prefers_email" checked="checked">
                <span class="option-display_text">
                    Email
                </span>
            </label>
        </li>
        <li>
            <label class="field-option_label">
                <input type="checkbox" name="contact_preferences" value="prefers_sms" checked="checked">
                <span class="option-display_text">
                    Text Message
                </span>
            </label>
        </li>
        <li>
            <label class="field-option_label">
                <input type="checkbox" name="contact_preferences" value="prefers_snailmail">
                <span class="option-display_text">
                    Paper mail
                </span>
            </label>
        </li>
        <li>
            <label class="field-option_label">
                <input type="checkbox" name="contact_preferences" value="prefers_voicemail">
                <span class="option-display_text">
                    Voicemail
                </span>
            </label>
        </li>
        </ul>
    </div>
    """
        self.assertHTMLEqual(results, expected)





