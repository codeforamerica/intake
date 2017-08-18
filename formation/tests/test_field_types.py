import inspect
import datetime
from unittest import TestCase

from formation.tests import mock
from formation.tests import sample_answers

from formation.tests.utils import PatchTranslationTestCase, django_only

from formation import field_types, exceptions, fields
from formation.field_base import Field

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


class Ducks(field_types.IntegerField):
    context_key = "ducks"


class MultipleFruit(field_types.MultipleChoiceField):
    context_key = "fruit"
    choices = (
        ('apples', 'Apples'),
        ('oranges', 'Oranges'))


class IsOkayWithPizza(field_types.ConsentCheckbox):
    context_key = "okay_with_pizza"
    label = "Is pizza okay for dinner?"
    display_text = "Is okay with pizza"
    is_required_error_message = "We're sorry, but pizza is the only option."
    agreement_text = "Yes, I am okay with pizza"


class TestCharField(PatchTranslationTestCase):

    def test_handles_multivaluedict_properly(self):
        single, multi, empty, blank, missing = mock.get_multivalue_examples(
            'name', ['Croissant', 'Marzipan'])
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

    def test_doesnt_escape_html(self):
        unescaped = "T'Pring"
        field = NameField({'name': unescaped})
        escaped = 'T&#39;Pring'
        field.is_valid()
        self.assertEqual(field.get_current_value(), unescaped)
        self.assertNotEqual(field.get_current_value(), escaped)
        self.assertIn(escaped, field.display())


def get_validated_monthly_income_field_with(input_value):
    data = {'monthly_income': input_value}
    field = fields.MonthlyIncome(data)
    field.is_valid()
    return field


class TestIntegerField(PatchTranslationTestCase):

    def test_is_okay_with_unset_raw_value(self):
        field = Ducks({})
        field.is_valid()
        self.assertIsNone(field.get_current_value())

    def test_parse_monthly_income(self):
        test_data = sample_answers.number_pairs
        for sample_input, expected_result in test_data.items():
            data = {'ducks': sample_input}
            field = Ducks(data)
            field.is_valid()
            self.assertEqual(field.parsed_data, expected_result)

    def test_get_current_value_none_if_empty(self):
        field = Ducks()
        self.assertIsNone(field.get_current_value())

    def test_adds_parse_error_if_given_misc_string(self):
        field = Ducks({'ducks': 'Not sure'})
        self.assertFalse(field.is_valid())
        expected_error = ("You entered 'Not sure', which doesn't "
                          "look like a number")
        self.assertIn(expected_error, field.get_errors_list())


class TestWholeDollarField(PatchTranslationTestCase):

    def test_is_okay_with_unset_raw_value(self):
        field = fields.MonthlyIncome({})
        field.is_valid()
        self.assertIsNone(field.get_current_value())

    def test_parse_monthly_income(self):
        test_data = sample_answers.dollar_answer_pairs
        for sample_input, expected_result in test_data.items():
            data = {'monthly_income': sample_input}
            field = fields.MonthlyIncome(data)
            field.is_valid()
            self.assertEqual(field.parsed_data, expected_result)

    def test_comma_display(self):
        """WholeDollarField.get_display_value() 1000 -> $1,000.00
        """
        field = get_validated_monthly_income_field_with(1000)
        self.assertEqual(field.get_display_value(), "$1,000.00")

    def test_simple_display(self):
        """WholeDollarField.get_display_value() 20 -> $20.00
        """
        field = get_validated_monthly_income_field_with(20)
        self.assertEqual(field.get_display_value(), "$20.00")

    def test_negative_display(self):
        """WholeDollarField.get_display_value() -20 -> -$20.00
        """
        field = get_validated_monthly_income_field_with(-20)
        self.assertEqual(field.get_display_value(), "$-20.00")

    def test_get_current_value_int_if_not_empty(self):
        """WholeDollarField.get_current_value() returns int
        """
        field = get_validated_monthly_income_field_with(5)
        self.assertEqual(type(field.get_current_value()), int)

    def test_get_current_value_none_if_empty(self):
        """WholeDollarField.get_current_value() None if empty
        """
        field = fields.MonthlyIncome()
        self.assertIsNone(field.get_current_value())

    def test_adds_parse_error_if_given_misc_string(self):
        """'Not sure' --> error
        """
        field = get_validated_monthly_income_field_with('Not sure')
        expected_error = ("You entered 'Not sure', which doesn't "
                          "look like a dollar amount")
        self.assertIn(expected_error, field.get_errors_list())


class TestDateTimeField(PatchTranslationTestCase):
    example_datetime = datetime.datetime(2016, 4, 18)

    def as_input(self, thing):
        return {DateReceived.context_key: thing}

    def test_is_okay_with_unset_raw_value(self):
        field = DateReceived({})
        field.is_valid()
        self.assertTrue(field.get_current_value() is None)

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


class TestPhoneNumberField(PatchTranslationTestCase):

    def test_is_okay_with_unset_raw_value(self):
        field = fields.PhoneNumberField({})
        field.is_valid()
        self.assertEqual(field.get_current_value(), '')

    def test_parse_phone_number(self):
        test_data = sample_answers.phone_number_answer_pairs
        for sample_input, expected_result in test_data.items():
            data = {'phone_number': sample_input}
            field = fields.PhoneNumberField(data)
            field.is_valid()
            self.assertEqual(field.parsed_data, expected_result)

    def test_get_current_value_is_empty_string_if_empty(self):
        field = fields.PhoneNumberField()
        self.assertEqual(field.get_current_value(), '')

    def test_get_display_value_is_empty_string_if_empty(self):
        field = fields.PhoneNumberField()
        self.assertEqual(field.get_display_value(), '')

    def test_get_display_value_has_correct_format(self):
        field = fields.PhoneNumberField({'phone_number': '8884445555'})
        field.is_valid()
        self.assertEqual(field.get_display_value(), '(888) 444-5555')

    def test_get_display_value_handles_invalid_numbers(self):
        test_data = sample_answers.phone_number_display_pairs
        for data, expected in test_data.items():
            with self.subTest(data=data, expected=expected):
                field = fields.PhoneNumberField({'phone_number': data})
                field.is_valid()
                self.assertEqual(expected, field.get_display_value())

    def test_adds_parse_error_if_given_misc_string(self):
        field = fields.PhoneNumberField({'phone_number': 'Not sure'})
        self.assertFalse(field.is_valid())
        expected_error = ("You entered 'Not sure', which doesn't "
                          "look like a valid phone number")
        self.assertIn(
            expected_error, [str(e) for e in field.get_errors_list()])


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
            NoChoices()


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
            NoChoices()


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
        'day': 2,
        'year': 1982,
        'month': 12
    }
    empty_value = {
        'day': None,
        'year': None,
        'month': None
    }
    missing_month_value = {
        'day': 2,
        'year': 1982,
        'month': None
    }

    missing_subkey = {'dob': {
        'day': 2,
        'year': 1982,
    }}
    incorrect_subkey = {'dob': {
        'day': 2,
        'year': 1982,
        'apple': 12,
    }}
    dotsep_incorrect_subkey = {
        'dob.day': 2,
        'dob.year': 1982,
        'dob.apple': 12, }
    dotsep_missing_subkey = {
        'dob.day': 2,
        'dob.year': 1982}

    def assertParsesCorrectly(
            self, field, expected_output, subfield_vals=[12, 2, 1982]):
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
            self.assertParsesCorrectly(
                field, self.empty_value, [None, None, None])

    def test_can_be_instantiated_with_preparsed_data(self):
        prestructured = {'dob': {
            'day': 2,
            'year': 1982,
            'month': 12
        }}
        dotsep = {
            'dob.year': 1982,
            'dob.day': 2,
            'dob.month': 12,
        }
        undersep = {
            'dob_year': 1982,
            'dob_day': 2,
            'dob_month': 12,
        }
        for input_data in [prestructured, dotsep, undersep]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(field, self.parsed_value)

    def test_valid_with_missing_subkey(self):
        for input_data in [self.missing_subkey, self.dotsep_missing_subkey]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(
                field, self.missing_month_value, [
                    None, 2, 1982])

    def test_valid_with_incorrect_subkey(self):
        for input_data in [self.incorrect_subkey,
                           self.dotsep_incorrect_subkey]:
            field = fields.DateOfBirthField(input_data)
            self.assertParsesCorrectly(
                field, self.missing_month_value, [
                    None, 2, 1982])

    def test_required_only_fails_with_all_missing_data(self):
        only_one = {
            'dob.day': '2',
        }
        field = fields.DateOfBirthField(only_one)
        self.assertParsesCorrectly(field,
                                   {'year': None, 'month': None, 'day': 2},
                                   [None, 2, None])
        self.assertFalse(field.is_empty())

        blank = {
            'dob.year': None,
            'dob.day': None,
            'dob.month': None,
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
            BadMulti()


class TestConsentCheckbox(TestCase):

    @django_only
    def test_has_expected_choices(self):
        field = IsOkayWithPizza()
        expected_choices = ((field_types.YES, "Yes, I am okay with pizza"),)
        self.assertEqual(field.choices, expected_choices)

    @django_only
    def test_errors_when_unset(self):
        field = IsOkayWithPizza({}, required=True)
        self.assertFalse(field.is_valid())
        expected_error = "We're sorry, but pizza is the only option."
        self.assertIn(expected_error, field.get_errors_list())

    @django_only
    def test_errors_when_empty(self):
        field = IsOkayWithPizza({'okay_with_pizza': ''}, required=True)
        self.assertFalse(field.is_valid())
        expected_error = "We're sorry, but pizza is the only option."
        self.assertIn(expected_error, field.get_errors_list())

    @django_only
    def test_renders_with_checkbox(self):
        field = IsOkayWithPizza()
        self.assertIn('type="checkbox"', field.render())

    @django_only
    def test_works_with_yes(self):
        field = IsOkayWithPizza({'okay_with_pizza': field_types.YES})
        self.assertTrue(field.is_valid())

    @django_only
    def test_minimal_spec(self):

        class TinyConsent(field_types.ConsentCheckbox):
            context_key = "is_okay"
            label = "Is okay?"

        field = TinyConsent({})
        self.assertFalse(field.is_valid())
        expected_choices = ((field_types.YES, "Yes"),)
        self.assertEqual(field.choices, expected_choices)
        expected_error = Field.is_required_error_message
        self.assertIn(expected_error, field.get_errors_list())


class TestRenderFieldTypes(TestCase):

    @django_only
    def test_render_charfield(self):
        field = NameField()
        rendered = field.render()
        self.assertEqual(rendered, str(field))
        self.assertTrue(hasattr(rendered, '__html__'))

    @django_only
    def test_render_datetimefield(self):
        field = DateReceived()
        rendered = field.render()
        self.assertEqual(rendered, str(field))
        self.assertTrue(hasattr(rendered, '__html__'))

    @django_only
    def test_render_choicefield(self):
        field = SingleFruit()
        self.assertEqual(field.render(), str(field))
        self.assertTrue(hasattr(field.render(), '__html__'))

    @django_only
    def test_render_multiplechoicefield(self):
        field = MultipleFruit()
        self.assertEqual(field.render(), str(field))
        self.assertTrue(hasattr(field.render(), '__html__'))
