from django.test import TestCase
from intake.validators import template_field_renders_correctly, ValidationError


class TestTemplateFieldValidator(TestCase):

    fixtures = ['counties', 'organizations']

    def test_reports_compilation_error(self):
        with self.assertRaises(ValidationError):
            template_field_renders_correctly("{% if something %}")

    def test_reports_render_error(self):
        with self.assertRaises(ValidationError):
            template_field_renders_correctly(
                "{{ county.nonexistent_method() }}")

    def test_validates_good_template(self):
        template_field_renders_correctly("""
            {{ county.capitalize() }}
            {{ organization_contact_message.upper() }}
            {{ personal_statement_link.lower() }}
            {{ letters_of_rec_link.lower() }}
            """)
