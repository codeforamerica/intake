from unittest import TestCase
from unittest.mock import Mock, patch

from intake.forms import form_base
from intake.forms import fields as F
from intake.serializer_forms import Form


class TestCombinableForm(TestCase):
    sample_full_kwargs = dict(
        counties=['yolo', 'santacruz'],
        fields=set([
            F.dob,
            F.first_name,
            F.address
        ]),
        required_fields=(
            F.first_name,
            F.dob),
        recommended_fields={F.address},
        unused_kwarg='anything'
    )

    def setUp(self):

        class FormA(form_base.CombinableForm):
            counties = {'sanfrancisco'}
            fields = {
                F.contact_preferences,
                F.us_citizen,
                F.address,
            }
            required_fields = {
                F.address
            }

        class FormB(form_base.CombinableForm):
            counties = {'contracosta'}
            fields = {
                F.first_name,
                F.email,
                F.address
            }
            required_fields = {
                F.email,
                F.address
            }
            recommended_fields = {
                F.first_name
            }

        self.form_class_a = FormA
        self.form_class_b = FormB

    def test_init(self):
        result = form_base.CombinableForm(**self.sample_full_kwargs)
        self.assertFalse(hasattr(result, 'unused_kwarg'))
        for attribute in result.combinable_set_attributes:
            # all the attributes should be set on the object
            self.assertTrue(hasattr(result, attribute))
            # all the init attributes should be coerced to
            # `set()` objects
            value = getattr(result, attribute)
            self.assertEqual(type(value), set)

    def test_inheritance(self):
        form = self.form_class_a()
        self.assertEqual(form.counties, {'sanfrancisco'})
        self.assertEqual(form.fields,
                         {F.contact_preferences, F.us_citizen, F.address})
        self.assertEqual(form.required_fields, {F.address})
        self.assertFalse(hasattr(form, 'recommended_fields'))

    def test_add_two_forms(self):
        # instantiate the two forms
        # testing the expected instantiation should be covered
        # in the above tests
        # okay
        form_a = self.form_class_a()
        form_b = self.form_class_b()
        # combine the two forms
        combined = form_a | form_b
        # make sure the resulting combined form is
        # the right type with the right attributes
        self.assertEqual(type(combined), form_base.CombinableForm)
        self.assertEqual(combined.counties,
                         {'sanfrancisco', 'contracosta'})
        self.assertEqual(combined.fields, {
            F.first_name,
            F.contact_preferences,
            F.email,
            F.us_citizen,
            F.address
        })
        self.assertEqual(combined.required_fields, {
            F.email, F.address
        })
        self.assertEqual(combined.recommended_fields, {
            F.first_name
        })

    def test_can_return_serializer_form_instance(self):
        # instantiate a form
        form_a = self.form_class_a()
        form_instance = form_a.get_validation_form_instance()
        self.assertEqual(form_instance.__class__.__name__, 'ValidatableForm')
        self.assertTrue(isinstance(form_instance, Form))
