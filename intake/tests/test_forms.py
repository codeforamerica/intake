from django.test import TestCase
from django.utils import html as html_utils

from intake import forms, validators
from intake.tests import mock

class TestForms(TestCase):

    def test_application_form_with_mock_answers(self):
        # Should work with a set of mock answers
        fake_answers = mock.form_answers()
        form = forms.ClearMyRecordSFForm(fake_answers)
        self.assertTrue(form.is_valid())

    def test_application_form_with_raw_empty_post_data(self):
        # Application form should not have trouble reading raw post data from
        # a Django request. But the form should not be valid
        form = forms.ClearMyRecordSFForm(mock.RAW_FORM_DATA)
        self.assertTrue(not form.is_valid())
        keys = form.errors.keys()
        self.assertTrue('first_name' in keys)
        self.assertTrue('last_name' in keys)
        self.assertEqual(len(keys), 2)

    def test_preferred_contact_info_validation(self):
        contact_preferences = [
                "prefers_email",
                "prefers_sms",
                "prefers_snailmail",
                "prefers_voicemail"
        ]
        form = forms.ClearMyRecordSFForm(dict(
            contact_preferences=contact_preferences
            ))
        error_messages = [
            validators.gave_preferred_contact_methods.message(k)
            for k in contact_preferences
            ]
        self.assertFalse(form.is_valid())
        errors = form.errors
        self.assertIn(validators.gave_preferred_contact_methods.message('prefers_sms'), errors['phone_number'])
        self.assertIn(validators.gave_preferred_contact_methods.message('prefers_voicemail'), errors['phone_number'])
        self.assertIn(validators.gave_preferred_contact_methods.message('prefers_email'), errors['email'])
        self.assertIn(validators.gave_preferred_contact_methods.message('prefers_snailmail'), errors['address'])
        # case: only required errors, no contact info erros
        form = forms.ClearMyRecordSFForm(mock.post_data(**{
            'contact_preferences': contact_preferences,
            'address.street': '111 Main St.',
            'address.city': 'Oakland',
            'address.state': 'CA',
            'address.zip': '94609',
            'phone_number': '415-333-4444',
            'email': 'someone@gmail.com'
            }))
        self.assertFalse(form.is_valid())
        self.assertFalse('phone_number' in form.errors)
        self.assertFalse('email' in form.errors)
        self.assertFalse('address' in form.errors)


    def test_contact_info_validation_errors_dont_override_field_errors(self):
        contact_preferences = [
                "prefers_email",
                "prefers_sms",
        ]
        form = forms.ClearMyRecordSFForm(data=dict(
            first_name="Foo",
            last_name="Bar",
            email="not_good_gmail",
            contact_preferences=contact_preferences
            ))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('phone_number', form.errors)


    def test_name_is_minimal_requirement(self):
        """Application form should be valid with nothing but a name
            Should not be valid with any empty name inputs
        """
        # valid with name only
        form = forms.ClearMyRecordSFForm(
            dict(first_name="Foo", last_name="Bar"))
        self.assertTrue(form.is_valid())
        self.assertTrue(form.warnings)

        # invalid if missing either last or first name
        form = forms.ClearMyRecordSFForm(
            dict(first_name=" ", last_name="Bar"))
        self.assertTrue(not form.is_valid())
        self.assertTrue(form.warnings)

        form = forms.ClearMyRecordSFForm(
            dict(first_name="Foo", last_name=" "))
        self.assertTrue(not form.is_valid())
        self.assertTrue(form.warnings)

    def test_gives_warning_for_missing_ssn(self):
        fake_answers = mock.form_answers()
        fake_answers['ssn'] = ' '
        form = forms.ClearMyRecordSFForm(fake_answers)
        if form.is_valid():
            warnings = form.warnings
            self.assertIn('ssn', warnings)
            self.assertListEqual(warnings['ssn'], [forms.Warnings.SSN])

    def test_gives_warning_for_missing_dob(self):
        fake_answers = mock.form_answers()
        fake_answers['dob.day'] = ' '
        form = forms.ClearMyRecordSFForm(fake_answers)
        if form.is_valid():
            warnings = form.warnings
            self.assertIn('dob', warnings)
            self.assertListEqual(warnings['dob'], [forms.Warnings.DOB])

    def test_gives_warning_for_missing_address(self):
        fake_answers = mock.form_answers()
        fake_answers['address.street'] = ' '
        form = forms.ClearMyRecordSFForm(fake_answers)
        if form.is_valid():
            warnings = form.warnings
            self.assertIn('address', warnings)
            self.assertListEqual(warnings['address'], [forms.Warnings.ADDRESS])

    def test_form_render_is_equivalent_to_previous_form(self):
        from django.template import loader
        fake_answers = mock.form_answers()
        fake_answers['contact_preferences'] = ['prefers_email', 'prefers_sms']
        form = forms.ClearMyRecordSFForm(fake_answers)
        context = {'form': form}
        result = loader.get_template('apply_page.jinja').render(context)

    def test_check_options_macro(self):
        from django.template import loader
        jinja = loader.engines['jinja']
        template = jinja.env.from_string("""{% import 'macros.jinja' as macros -%}
        {{- macros.checkbox_options_field(form.fields.contact_preferences) -}}
        """)
        fake_answers = mock.form_answers(contact_preferences=['prefers_email', 'prefers_sms'])
        form = forms.ClearMyRecordSFForm(fake_answers)
        field = form.fields['contact_preferences']
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

    def test_radio_select_macro(self):
        from django.template import loader
        jinja = loader.engines['jinja']
        template = jinja.env.from_string("""{% import 'macros.jinja' as macros -%}
        {{- macros.radio_select_field(form.fields.currently_employed) -}}
        """)
        fake_answers = mock.form_answers(currently_employed='yes')
        form = forms.ClearMyRecordSFForm(fake_answers)
        field = form.fields['currently_employed']
        context = {'form': form}
        results = template.render(context)
        expected = """
    <div class="field field-radio_options currently_employed">
    <legend>
        Are you currently employed?
    </legend>
    <ul class="radio_options options_list">
        <li>
            <label class="field-option_label">
                <input type="radio" name="currently_employed" value="yes" checked="checked">
                <span class="option-display_text">
                    Yes
                </span>
            </label>
        </li>
        <li>
            <label class="field-option_label">
                <input type="radio" name="currently_employed" value="no">
                <span class="option-display_text">
                    No
                </span>
            </label>
        </li>
    </ul>
</div>
    """
        self.assertHTMLEqual(results, expected)


    def test_emailfield(self):
        form = forms.ClearMyRecordSFForm(data={
            'email': ''
            })
        self.assertFalse(form.is_valid())
        self.assertFalse('email' in form.errors)

    def test_addressfield(self):
        form = forms.ClearMyRecordSFForm(
            mock.post_data(**{
                'contact_preferences': ['prefers_snailmail', 'prefers_email'],
                'address.street': '111 Main St.',
                'address.city': 'Oakland',
                'address.state': 'CA',
                'address.zip': '94609'
                }))
        self.assertFalse(form.is_valid())
        self.assertFalse('address' in form.errors)
        field = form.fields['address']
        self.assertEqual(str(field.current_value()), "<Address(city='Oakland', state='CA', street='111 Main St.', zip='94609')>")

    def test_current_value(self):
        data = {
                'first_name': 'Foo',
                'last_name': 'Bar',
                'contact_preferences': ['prefers_snailmail', 'prefers_email'],
                'address.street': '111 Main St.',
                'address.city': 'Oakland',
                'address.state': 'CA',
                'address.zip': '94609',
                'dob.month': '5',
                'dob.day': '21',
                'dob.year': '80',
                'email': 'someone@gmail.com',
                }
        form = forms.ClearMyRecordSFForm(mock.post_data(**data))
        field = form.fields['address']
        self.assertEqual(
            str(field.current_value()),
            "<Address(city='Oakland', state='CA', street='111 Main St.', zip='94609')>")
        self.assertEqual(field.fields['street'].current_value(), '111 Main St.')
        self.assertEqual(field.fields['city'].current_value(), 'Oakland')
        self.assertEqual(field.fields['city'].input_name(), 'address.city')
        self.assertEqual(field.fields['city'].class_name(), 'address_city')
        self.assertEqual(form.fields['first_name'].input_name(), 'first_name')
        form = forms.ClearMyRecordSFForm()
        for name, field in form.fields.items():
            self.assertEqual(field.current_value(), field.get_empty_value())


class TestContraCostaCleanSlateForm(TestCase):

    def test_correct_fields_are_required(self):
        required_fields = [
            'first_name',
            'last_name',
            'dob',
            'us_citizen',
            'address',
            'on_parole',
            'on_probation',
            'currently_employed',
            'monthly_income',
            'income_source',
            'monthly_expenses',
        ]
        form = forms.ContraCostaCleanSlateForm()
        for name, field in form.fields.items():
            if name in required_fields:
                self.assertTrue(field.required, name)
