from formation import base, exceptions
from django.utils.translation import ugettext_lazy as _


class Field(base.BindParseValidate):
    """Fields are responsible for 
     - pulling their data from raw HTTP post data
     - having a clear `name` to use for html inputs
     - accessing their raw data
     - accessing their parsed data
     - determining if they are required
     - having validators
     - storing errors
     - having defaults
     - having labels
     - having help_text
     - having defined empty values
    """
    is_multivalue = False
    is_required_error_message = _("This field is required.")
    is_recommended_error_message = _("Leaving this field blank might cause problems.")
    empty_value = base.UNSET
    template_name = "formation/text_input.jinja"
    display_template_name = "formation/default_input_display.jinja"

    def __init__(self, *args, form=None, required=True, recommended=False,
        optional=False, is_subfield=False, label=None, **kwargs):
        """Sets the `required` attribute for this field.
        """
        super().__init__(*args, **kwargs)
        self.form = form
        self.required = required
        self.recommended = recommended
        # required should override optional
        self.optional = optional if not (required or recommended) else False
        self.is_subfield = is_subfield
        self.template = None
        if not hasattr(self, 'label'):
            self.label = label or self.context_key.capitalize()

    def get_input_name(self):
        """Return a key that can be used to extract
        raw data from a dict or http post of all fields.
        The key should be unique to this field, and is used 
        for the `name` attribute in html inputs.
        """
        if self.parent:
            return '.'.join([self.parent.context_key, self.context_key])
        return self.context_key

    def assert_parse_received_correct_type(self, raw_value, type_):
        """Checks that the raw data is an expected type. In some fields,
        if the raw input data is not a particular type, it is an indication
        that the field is being used incorrectly
        """
        message_template = "`{}` needed a `{}` object for parsing. Received a `{}`"
        if not isinstance(raw_value, type_):
            raise TypeError(message_template.format(
                self.__repr__, type_, type(raw_value)))

    def get_html_class_name(self):
        """Returns the input name of this field, using underscores
        in place of `.` as a field 
        """
        return self.get_input_name().replace('.', '_')

    def extract_raw_value(self, raw_data):
        """Pulls the relevant data from an http post, multi-value-dict,
        or dict should be called within self.parse() after initialization
        First, it will attempt to use `.get_input_name()` to generate
        a key for extracting the raw value, if that key does not exist,
        it will fall back to `.context_key`, and if that fails, it will
        set `.raw_value` to `formation.base.UNSET` to indicate that the
        value was not found.
        """
        fallback = raw_data.get(
            self.context_key, base.UNSET)
        alternate_input = raw_data.get(
            self.get_html_class_name(), fallback)
        return raw_data.get(
            self.get_input_name(), alternate_input)

    def parse_and_validate(self, raw_data):
        """Fields must pull their raw inputs out of an
        HTTP post or dictionary before running parsing and validation
        """
        if not isinstance(raw_data, dict):
            raise exceptions.RawDataMustBeDictError(
                "The raw data passed to `{}` was `{}` type, not dict.".format(
                    self, type(raw_data))\
                + " Raw data passed to forms and fields must be an instance of dict."
            )
        self.raw_input_value = self.extract_raw_value(raw_data)
        super().parse_and_validate(self.raw_input_value)

    def is_empty(self):
        """This checks self.parsed_data against self.empty_value
        """
        return self.parsed_data == self.empty_value

    def validate(self):
        """Checks whether it is empty before
        running any other validators. It only runs the
        remaining validators, using `super().validate()`,
        if it is not required or it has a required input.
        """
        if self.is_empty():
            if self.required:
                self.add_error(self.is_required_error_message)
            elif self.recommended:
                self.add_warning(self.is_recommended_error_message)
        else:
            super().validate()

    def get_current_value(self):
        """Returns the value for this field, based on 
        """
        if self.parsed_data is not base.UNSET:
            return self.parsed_data
        else:
            return self.empty_value

    def get_template_context(self, context):
        """Add `self` as `field` in render context"""
        context = super().get_template_context(context)
        context['field'] = self
        return context

    def get_display_label(self):
        if hasattr(self, 'display_label'):
            return self.display_label
        return self.context_key.capitalize().replace('_', ' ')

    def get_display_value(self):
        return self.get_current_value()



