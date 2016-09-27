import inspect
import datetime
from unittest import TestCase
from unittest.mock import Mock, patch
from formation.tests import mock
from formation.tests.utils import PatchTranslationTestCase, django_only

from formation import field_types, exceptions, fields

from django.utils.datastructures import MultiValueDict


class NameField(field_types.CharField):
    context_key = "name"
    label = "Name"
    help_text = "What should we call you?"


class DateReceived(field_types.DateTimeField):
    default_display_format = "%Y-%m-%d"
    context_key = "received"


class SingleFruit(field_types.ChoiceField):
    context_key = "fruit"
    choices = (
        ('apples', 'Apples'),
        ('oranges', 'Oranges'))


class MultipleFruit(field_types.MultipleChoiceField):
    context_key = "fruit"
    choices = (
        ('apples', 'Apples'),
        ('oranges', 'Oranges'))


class TestCharField(PatchTranslationTestCase):

    def test_handles_multivaluedict_properly(self):
        single, multi, empty, blank, missing = mock.get_multivalue_examples(
            'name', ['Croissant','Marzipan'])
        for input_data in [single, multi]:
            field = NameField(input_data)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), 'Marzipan')

        for input_data in [empty, blank, missing]:
            field = NameField(input_data)
            self.assertFalse(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

        for input_data in [empty, blank, missing]:
            field = NameField(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

    def test_can_be_instantiated_with_preparsed_data(self):
        valid, invalid, blank, missing = mock.get_dict_examples(
            'name', 'Marzipan', None)
        field = NameField(valid)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), 'Marzipan')
        for input_data in [blank, missing]:
            field = NameField(input_data)
            self.assertFalse(field.is_valid())
            self.assertEqual(field.get_current_value(), '')
        for input_data in [blank, missing]:
            field = NameField(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

    def test_raises_error_if_given_something_thats_not_a_string(self):
        field = NameField({'name': 4})
        with self.assertRaises(TypeError):
            field.is_valid()

    def test_default_empty_value_is_a_string(self):
        field = NameField()
        self.assertEqual(field.get_current_value(), '')

    def test_whitespace_characters_are_stripped_during_parse(self):
        field = NameField({'name': ' \nMarzipan\r \t '})
        self.assertTrue(field.is_valid())
        self.assertFalse(field.errors)
        self.assertEqual(field.get_current_value(), 'Marzipan')

    def test_can_shut_off_stripping(self):
        class WhitespaceField(field_types.CharField):
            context_key = "whitespace"
            should_strip_input = False
        field = WhitespaceField({"whitespace": "\n \t\r"})
        self.assertTrue(field.is_valid())
        self.assertFalse(field.is_empty())
        self.assertEqual(field.get_current_value(), "\n \t\r")


class TestDateTimeField(PatchTranslationTestCase):
    example_datetime = datetime.datetime(2016, 4, 18)

    def as_input(self, thing):
        return {DateReceived.context_key: thing}

    def test_parses_datetime_unchanged(self):
        dt = self.as_input(self.example_datetime)
        field = DateReceived(dt)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), self.example_datetime)
        self.assertEqual(field.parsed_data, self.example_datetime)

    def test_parses_strings_using_dateutil(self):
        datestrings = [
            "2016-04-18",
            "4/18/2016"]
        for datestring in datestrings:
            field = DateReceived(self.as_input(datestring))
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), self.example_datetime)
            self.assertEqual(field.parsed_data, self.example_datetime)

    def test_adds_error_for_bad_text(self):
        badstrings = [
            "9ans09dn"
            "1324/314123"
            "2/15"]
        for badstring in badstrings:
            field = DateReceived(self.as_input(badstring))
            self.assertFalse(field.is_valid())

    def test_raises_error_if_not_datetime_or_str(self):
        bad_inputs = [[], {}, 5]
        for bad_input in bad_inputs:
            with self.assertRaises(TypeError):
                field = DateReceived(self.as_input(bad_input))
                field.is_valid()

    def test_get_display_value_returns_string(self):
        inputs = [
            self.example_datetime,
            '4/18/2016',
            '']
        for input_sample in inputs:
            field = DateReceived(self.as_input(input_sample))
            field.is_valid()
            is_str = isinstance(field.get_display_value(), str)
            self.assertTrue(is_str)

    def test_can_override_default_display_format(self):
        field = DateReceived({'received': '4/18/2016'})
        field.is_valid()
        self.assertEqual(field.get_display_value(), '2016-04-18')


class TestChoiceField(PatchTranslationTestCase):

    def test_handles_multivaluedict_properly(self):
        single, multi, empty, blank, missing = mock.get_multivalue_examples(
            'fruit', ['oranges', 'apples'])

        for input_data in [single, multi]:
            field = SingleFruit(input_data)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), 'apples')

        for input_data in [empty, blank, missing]:
            field = SingleFruit(input_data)
            self.assertFalse(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

        for input_data in [empty, blank, missing]:
            field = SingleFruit(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

    def test_can_be_instantiated_with_preparsed_data(self):
        valid, invalid, blank, missing = mock.get_dict_examples(
            'fruit', 'apples', 'bananas')

        field = SingleFruit(valid)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), 'apples')

        field = SingleFruit(invalid)
        self.assertFalse(field.is_valid())
        self.assertEqual(field.get_current_value(), 'bananas')

        for input_data in [blank, missing]:
            field = SingleFruit(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

    def test_default_empty_value_is_a_string(self):
        field = SingleFruit()
        self.assertEqual(field.get_current_value(), '')

    def test_raises_error_if_instantiated_without_choices(self):
        class NoChoices(field_types.ChoiceField):
            pass
        with self.assertRaises(exceptions.NoChoicesGivenError):
            field = NoChoices()



class TestMultipleChoiceField(PatchTranslationTestCase):

    def test_handles_multivaluedict_properly(self):
        single, multi, empty, blank, missing = mock.get_multivalue_examples(
            'fruit', ['oranges', 'apples'])

        field = MultipleFruit(single)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), ['apples'])

        field = MultipleFruit(multi)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), ['oranges', 'apples'])

        for input_data in [empty, blank, missing]:
            field = MultipleFruit(input_data)
            self.assertFalse(field.is_valid())
            self.assertEqual(field.get_current_value(), [])

        for input_data in [empty, blank, missing]:
            field = MultipleFruit(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), [])

    def test_can_be_instantiated_with_preparsed_data(self):
        valid, invalid, blank, missing = mock.get_dict_examples(
            'fruit', ['oranges', 'apples'], ['bananas'])

        field = MultipleFruit(valid)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), ['oranges', 'apples'])

        field = MultipleFruit(invalid)
        self.assertFalse(field.is_valid())
        self.assertEqual(field.get_current_value(), ['bananas'])

        field = MultipleFruit(blank, required=False)
        with self.assertRaises(TypeError):
            field.is_valid()

        field = MultipleFruit(missing, required=False)
        self.assertTrue(field.is_valid())
        self.assertEqual(field.get_current_value(), [])

    def test_default_empty_value_is_an_empty_list(self):
        field = MultipleFruit()
        self.assertEqual(field.get_current_value(), [])

    def test_raises_error_if_instantiated_without_choices(self):
        class NoChoices(field_types.ChoiceField):
            pass
        with self.assertRaises(exceptions.NoChoicesGivenError):
            field = NoChoices()


class TestYesNoField(PatchTranslationTestCase):

    def test_handles_multivaluedict_properly(self):

        class IsThisAnArgument(field_types.YesNoField):
            context_key = 'is_an_argument'

        single, multi, empty, blank, missing = mock.get_multivalue_examples(
            'is_an_argument', ['no', 'yes'])

        for input_data in [single, multi]:
            field = IsThisAnArgument(input_data)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), 'yes')

        for input_data in [empty, blank, missing]:
            field = IsThisAnArgument(input_data)
            self.assertFalse(field.is_valid())
            self.assertEqual(field.get_current_value(), '')

        for input_data in [empty, blank, missing]:
            field = IsThisAnArgument(input_data, required=False)
            self.assertTrue(field.is_valid())
            self.assertEqual(field.get_current_value(), '')



class TestMultiValueField(PatchTranslationTestCase):
    parsed_value = {
                    'day': '2',
                    'year': '1982',
                    'month': '12'
                }
    empty_value = {
                    'day': '',
                    'year': '',
                    'month': ''
                }
    missing_month_value = {
                    'day': '2',
                    'year': '1982',
                    'month': ''
                }


    missing_subkey = {'dob': {
                    'day': '2',
                    'year': '1982',
                }}
    incorrect_subkey = {'dob': {
                    'day': '2',
                    'year': '1982',
                    'apple': '12',
                }}
    dotsep_incorrect_subkey = {
                'dob.day': '2',
                'dob.year': '1982',
                'dob.apple': '12',}
    dotsep_missing_subkey = {
                'dob.day': '2',
                'dob.year': '1982'}

    def assertParsesCorrectly(self, field, expected_output, subfield_vals=['12', '2', '1982']):
        self.assertTrue(field.is_valid())
        self.assertDictEqual(field.get_current_value(), expected_output)
        for subfield, value in zip(field.subfields, subfield_vals):
            self.assertTrue(subfield.is_valid())
            self.assertEqual(subfield.get_current_value(), value)

    def test_init_multivaluefield(self):
        field = fields.DateOfBirthField()
        self.assertTrue(hasattr(field, 'year'))
        self.assertTrue(hasattr(field, 'month'))
        self.assertTrue(hasattr(field, 'day'))
        self.assertEqual(field.empty_value, self.empty_value)
        # make sure all the subfields are instances
        for sub in field.subfields:
            self.assertFalse(inspect.isclass(sub))
            self.assertEqual(sub.required, False)
            self.assertEqual(sub.is_subfield, True)
            self.assertEqual(sub.parent, field)
            expected_sub = getattr(field, sub.context_key)
            self.assertEqual(sub, expected_sub)

    def test_parses_filled_multivalue_dicts(self):
        single = MultiValueDict({
            'dob.year': ['1982'],
            'dob.day': ['2'],
            'dob.month': ['12'],
            })
        multi = MultiValueDict({
            'dob.year': ['2000', '1982'],
            'dob.day': ['5', '2'],
            'dob.month': ['1', '12'],
            })
        for input_data in [single, multi]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(field, self.parsed_value)

    def test_parses_empty_multivalue_dicts(self):
        empty = MultiValueDict({
            'dob.year': [],
            'dob.day': [],
            'dob.month': [],
            })
        blank = MultiValueDict({
            'dob.year': [''],
            'dob.day': [''],
            'dob.month': [''],
            })
        missing = MultiValueDict({})
        for input_data in [empty, blank, missing]:
            field = fields.DateOfBirthField(input_data, required=False)
            self.assertParsesCorrectly(field, self.empty_value, ['','',''])

    def test_can_be_instantiated_with_preparsed_data(self):
        prestructured = {'dob': {
                            'day': '2',
                            'year': '1982',
                            'month': '12'
                            }}
        dotsep = {
            'dob.year': '1982',
            'dob.day': '2',
            'dob.month': '12',
            }
        undersep = {
            'dob_year': '1982',
            'dob_day': '2',
            'dob_month': '12',
            }
        for input_data in [prestructured, dotsep, undersep]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(field, self.parsed_value)

    def test_valid_with_missing_subkey(self):
        for input_data in [self.missing_subkey, self.dotsep_missing_subkey]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(field, self.missing_month_value, ['', '2', '1982'])

    def test_valid_with_incorrect_subkey(self):
        for input_data in [self.incorrect_subkey, self.dotsep_incorrect_subkey]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(field, self.missing_month_value, ['', '2', '1982'])

    def test_required_only_fails_with_all_missing_data(self):
        only_one = {
            'dob.day': '2',
            }
        field = fields.DateOfBirthField(only_one)
        self.assertParsesCorrectly(field,
            {'year': '', 'month': '', 'day': '2'},
            ['', '2', ''])
        self.assertFalse(field.is_empty())

        blank = {
            'dob.year': '',
            'dob.day': '',
            'dob.month': '',
            }
        missing = {}
        for input_data in [missing, blank]:
            field = fields.DateOfBirthField(input_data)
            self.assertFalse(field.is_valid())
            self.assertTrue(field.is_empty())
            self.assertEqual(field.get_current_value(), self.empty_value)

    def test_raises_error_when_instantiated_without_subfields(self):
        class BadMulti(field_types.MultiValueField):
            pass

        with self.assertRaises(exceptions.MultiValueFieldSubfieldError):
            field = BadMulti()



class TestRenderFieldTypes(TestCase):

    @django_only
    def test_render_charfield(self):
        field = NameField()
        self.assertEqual(field.render(), str(field))
        self.assertEqual(field.render(), mock.rendered.NAMEFIELD)

    @django_only
    def test_render_choicefield(self):
        field = SingleFruit()
        self.assertEqual(field.render(), str(field))
        self.assertEqual(field.render(), mock.rendered.FRUITSFIELD)

    @django_only
    def test_render_multiplechoicefield(self):
        field = MultipleFruit()
        self.assertEqual(field.render(), str(field))
        self.assertEqual(field.render(), mock.rendered.MULTIPLEFRUITSFIELD)

    @django_only
    def test_render_dateofbirthfield(self):
        field = fields.DateOfBirthField()
        self.assertEqual(field.render(), str(field))
        self.assertEqual(field.render(), mock.rendered.DATEOFBIRTHFIELD)
