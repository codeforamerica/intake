import re
import string
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from formation.field_base import Field
from formation.base import UNSET
from formation import exceptions, validators
from django.utils.translation import ugettext_lazy as _
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from project.jinja2 import oxford_comma
from dateutil.parser import parse as dateutil_parse
from datetime import datetime

YES = 'yes'
NO = 'no'
NOT_APPLICABLE = 'not_applicable'

YES_NO_CHOICES = (
    (YES, _('Yes')),
    (NO, _('No')),
)


def extract_digit_chars(input_string):
    return "".join(char for char in input_string if char in string.digits)


class CharField(Field):
    empty_value = ""
    should_strip_input = True

    def parse_as_text(self, raw_value):
        """Responsible for raising an error if the raw
        extracted value is not a string instance. If it recognizes
        the input as a string, use Django's `force_text` as an additional
        safety check. Strip the input based on `.should_strip_input`
        """
        self.assert_parse_received_correct_type(raw_value, str)
        if self.should_strip_input:
            return raw_value.strip()
        return raw_value

    def parse(self, raw_value):
        """CharFields check that input values are string types before
        stripping them of leading and trailing whitespace
        """
        value = self.empty_value
        if raw_value is not UNSET:
            raw_value = self.parse_as_text(raw_value)
        if raw_value:
            value = raw_value
        return value


class MultilineCharField(CharField):
    template_name = "formation/textarea_field.jinja"


class IntegerField(CharField):
    empty_value = None
    parse_error_message = _("You entered '{}', which "
                            "doesn't look like a number")
    # https://regex101.com/r/iM0xY3/1
    special_zero_pattern = re.compile(r"n\/a|none",
                                      flags=re.IGNORECASE)

    def parse_numeric_string(self, raw_value):
        special_zero = re.search(self.special_zero_pattern, raw_value)
        antedecimal, *postdecimal = raw_value.split('.')
        number = extract_digit_chars(antedecimal)
        if number:
            return int(number)
        elif special_zero:
            return 0
        else:
            self.add_error(self.parse_error_message.format(raw_value))
        return None

    def parse(self, raw_value):
        value = self.empty_value
        if raw_value is UNSET:
            return value
        if isinstance(raw_value, int) or raw_value is None:
            return raw_value
        if isinstance(raw_value, float):
            return round(raw_value)
        self.assert_parse_received_correct_type(raw_value, str)
        raw_value = self.parse_as_text(raw_value)
        if raw_value:
            value = self.parse_numeric_string(raw_value)
        return value


class WholeDollarField(IntegerField):
    empty_value = None
    # https://regex101.com/r/dP5wX1/2
    dollars_pattern = re.compile(r"(?P<dollars>[\d,]+)(?P<cents>[\.]\d\d?)?")
    parse_error_message = _("You entered '{}', which "
                            "doesn't look like a dollar amount")

    def parse_numeric_string(self, raw_value):
        # does not check for multiple separate dollar amounts
        possible_amount = re.search(self.dollars_pattern, raw_value)
        special_zero = re.search(self.special_zero_pattern, raw_value)
        if possible_amount:
            dollars = possible_amount.group('dollars')
            return int(dollars.replace(",", ""))
        elif special_zero:
            return 0
        else:
            self.add_error(self.parse_error_message.format(raw_value))
        return None

    def get_display_value(self):
        """should return $100.00
        """
        value = self.get_current_value()
        if value is None:
            return ''
        return "${}.00".format(intcomma(value))


class DateTimeField(CharField):
    """A DateTimeField takes an input string or datetime
    and stores a datetime value internally
    get_current_value will return either a datetime or None
    get_display_value will return an html safe string
    """
    empty_value = None
    default_display_format = "%c"
    parse_error_message = _("'{}' does not look like a date")

    def parse(self, raw_value):
        """If the input is already a datetime,
        pass it through. Otherwise, ensure that it is a str
        and use dateutil to parse it
        """
        value = self.empty_value
        if raw_value is UNSET:
            return value
        if isinstance(raw_value, datetime) or raw_value is None:
            return raw_value
        self.assert_parse_received_correct_type(raw_value, str)
        raw_value = self.parse_as_text(raw_value)
        if raw_value:
            try:
                value = dateutil_parse(raw_value)
            except ValueError:
                self.add_error(
                    self.parse_error_message.format(raw_value))
        else:
            value = None
        return value

    def get_display_value(self, strftime_format=None):
        if not strftime_format:
            strftime_format = self.default_display_format
        value = self.get_current_value()
        if value:
            value = value.strftime(strftime_format)
        else:
            value = ''
        return value


class PhoneNumberField(CharField):

    empty_value = ''
    parse_error_message = _("'{}' does not look like a valid phone number")

    def parse(self, raw_value):
        """CharFields check that input values are string types before
        stripping them of leading and trailing whitespace
        """
        value = self.empty_value
        if raw_value is not UNSET:
            self.assert_parse_received_correct_type(raw_value, str)
            raw_value = self.parse_as_text(raw_value)
        if raw_value:
            value = extract_digit_chars(raw_value)
            if not value:
                self.add_error(
                    self.parse_error_message.format(raw_value))
            try:
                value = self.parse_phone_number(value).national_number
            except NumberParseException as error:
                self.add_error(
                    self.parse_error_message.format(raw_value))
        return value

    def get_parsed_value(self, value=None):
        return self.parse_phone_number(self.get_current_value())

    def parse_phone_number(self, raw_string=None, country="US"):
        raw_string = raw_string or self.get_current_value()
        if raw_string:
            return phonenumbers.parse(raw_string, country)
        return self.empty_value

    def get_display_value(self):
        return phonenumbers.format_number(
            self.parse_phone_number(),
            phonenumbers.PhoneNumberFormat.NATIONAL)

    def get_tel_href(self):
        return "1" + self.get_parsed_value().national_number


class ChoiceField(CharField):
    validators = [validators.is_a_valid_choice]
    template_name = "formation/radio_select.jinja"

    def __init__(self, *args, **kwargs):
        """Asserts that this field has a choices attribute
        """
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'choices'):
            raise exceptions.NoChoicesGivenError(str(
                "This field requires a `choices` attribute."
            ))
        if not hasattr(self, 'choice_display_dict'):
            self.choice_display_dict = {
                key: display
                for key, display in self.choices
            }

    def get_display_value(self):
        return self.get_display_for_choice(
            self.get_current_value()
            )

    def get_display_for_choice(self, value):
        return self.choice_display_dict[value]

    def get_display_choices(self):
        if getattr(self, 'flip_display_choice_order', False):
            return reversed(self.choices)
        return self.choices

    def is_current_choice(self, choice_option):
        return self.get_current_value() == choice_option


class MultipleChoiceField(ChoiceField):
    empty_value = []
    validators = [validators.are_valid_choices]
    template_name = "formation/checkbox_select.jinja"

    def extract_raw_value(self, raw_data):
        """Attempts to pull a list from raw data
        """
        key = self.get_input_name()
        if hasattr(raw_data, 'getlist'):
            raw_value = raw_data.getlist(key, self.empty_value)
        else:
            raw_value = raw_data.get(key, self.empty_value)
        return raw_value

    def parse(self, raw_values):
        """MultipleChoiceFields need a list of strings in order to
        parse input correctly. Each string is stripped of leading
        and trailing whitespace. Empty strings are discarded.
        """
        self.assert_parse_received_correct_type(raw_values, list)
        values = []
        for raw_value in raw_values:
            value = self.parse_as_text(raw_value)
            if value:
                values.append(value)
        return values

    def get_display_value(self, use_or=False):
        return oxford_comma([
            self.get_display_for_choice(choice)
            for choice in self.get_current_value()
        ], use_or)


class YesNoField(ChoiceField):
    choices = YES_NO_CHOICES
    display_template_name = "formation/option_set_display.jinja"

    def __bool__(self):
        return self.get_current_value() == YES


class MultiValueField(Field):
    template_name = "formation/multivalue_field.jinja"

    def __init__(self, *args, **kwargs):
        """After initializing this object's basic field properties,
        this will:
          - initialize each subfield w/ `.build_subfield(subfield)`
          - replace `.subfields` classes with instances
          - define `.empty_value` based on subfields
        """
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'subfields'):
            raise exceptions.MultiValueFieldSubfieldError(
                "There is no defined behavior for a MultiValueField with no .subfields attribute")
        # build the subfields
        self.subfields = [
            self.build_subfield(subfield)
            for subfield in self.subfields]
        # build empty value
        self.empty_value = {
            sub.context_key: sub.empty_value
            for sub in self.subfields}

    def build_subfield(self, subfield_class):
        """Creates a subfield instance
        """
        instance = subfield_class(
            self.raw_input_data,
            required=False,
            is_subfield=True
        )
        instance.parent = self
        # this might error if a context_key is not a valid
        # python variable name
        setattr(self, instance.context_key, instance)
        return instance

    def extract_raw_value(self, raw_data):
        # self.raw_data should be a dict that is the subset
        # of child field keys
        raw_value = {}
        if self.context_key in raw_data:
            raw_data = raw_data[self.context_key]
        for sub in self.subfields:
            sub.raw_input_value = sub.extract_raw_value(raw_data)
            raw_value[sub.get_input_name()] = sub.raw_input_value
        return raw_value

    def parse(self, raw_value):
        # should create a dict with simplified child keys
        value = self.empty_value.copy()
        for sub in self.subfields:
            sub.parsed_data = sub.parse(sub.raw_input_value)
            value[sub.context_key] = sub.parsed_data
        return value

    def is_empty(self):
        """Returns `True` if all subfields are empty
        """
        return all(sub.is_empty() for sub in self.subfields)

    def validate(self):
        """Run validation method on each subfield,
        update `.errors` with `subfield.errors`,
        and then run the validators for this parent field
        """
        for sub in self.subfields:
            # runs validators on subfields
            sub.validate()
            self.errors.update(sub.errors)
        # runs own validators
        super().validate()

    def get_current_value(self):
        return {
            sub.context_key: sub.get_current_value()
            for sub in self.subfields
        }


class FormNote:
    """A simple type for including content with
    no input for forms, such as a brief statement.
    """
    content = ""
    template_string = '<div class="note field-form_note"><p>{}</p></div>'
    escape_content = False

    def __init__(self, *args, **kwargs):
        pass

    def escape(self):
        return conditional_escape(self.content)

    def get_content(self):
        if self.escape_content:
            return self.escape(self.content)
        return self.content

    def render(self):
        return mark_safe(self.template_string.format(self.get_content()))

    def __repr__(self):
        return 'FormNote(content="{}")'.format(self.get_content())

    def __str__(self):
        return self.render()
