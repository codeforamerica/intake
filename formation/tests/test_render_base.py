from unittest import TestCase
from formation.tests.utils import django_only

from formation import render_base
import django
from django.utils.html import escape, conditional_escape


class TestRenderable(TestCase):

    example_template = "formation/example.html"

    @django_only
    def test_compile_template(self):
        instance = render_base.Renderable()
        instance.template_name = self.example_template
        instance.compile_template()
        self.assertTrue(instance._template)
        self.assertTrue(
            isinstance(
                instance._template,
                django.template.backends.django.Template
            ))
        self.assertEqual(
            instance.render(
                message="Hello World"), "<span>Hello World</span>")

    @django_only
    def test_mark_safe(self):
        from formation.fields import FirstName
        first_name = FirstName(dict(first_name="Foo"))
        first_name.is_valid()
        render_result = first_name.render()
        self.assertTrue(hasattr(render_result, '__html__'))
        display_result = first_name.display()
        self.assertTrue(hasattr(display_result, '__html__'))

    @django_only
    def test_escape(self):
        from formation.fields import FirstName
        bad_string = '<script src="malicious.js">'
        escaped_bad_string = "&lt;script src=&quot;malicious.js&quot;&gt;"
        first_name = FirstName(dict(first_name=bad_string))
        first_name.is_valid()
        render_result = first_name.render()
        self.assertNotIn(bad_string, render_result)
        self.assertIn(escaped_bad_string, render_result)
        display_result = first_name.display()
        self.assertNotIn(bad_string, display_result)
        self.assertIn(escaped_bad_string, display_result)
