from unittest import TestCase
from formation.tests.utils import django_only

import django
from formation import render_base



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