from formation import base
from collections import OrderedDict


class Form(base.BindParseValidate):

    context_key = '__all__'
    template_name = "formation/generic_form.jinja"
    display_template_name = "formation/default_form_display.jinja"
    validators = []
    field_attributes = [
        'recommended_fields',
        'required_fields',
        'optional_fields'
    ]

    def __init__(self, *args, files=None, validate=False,
                 skip_validation=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = OrderedDict([
            (field_class.context_key, self.build_field(field_class))
            for field_class in self.fields])
        self._update_field_attributes_with_instances()
        self.empty_value = {
            field.context_key: field.empty_value
            for field in self.get_usable_fields()}
        self.cleaned_data = base.UNSET
        if validate and self.is_bound():
            self.parse_and_validate(self.raw_input_data)

    def _add_message(self, message_type, message, key=None):
        """For adding errors or warnings, they are added both to
        this form as well as to the relevant field, if it exists
        """
        super()._add_message(message_type, message, key)
        if key and key in self.fields:
            self.fields.get(key)._add_message(message_type, message, key)

    @classmethod
    def get_field_keys(cls):
        for field_class in cls.fields:
            yield field_class.context_key

    def get_possible_display(self, field_key):
        """Returns the display string of field_key, else an empty string
        """
        if field_key in self.fields:
            return self.fields[field_key].render(display=True)
        else:
            return ""

    def __getattr__(self, attribute):
        if attribute[-8:] == '_display':
            field_key = attribute[:-8]
            return self.get_possible_display(field_key)
        msg = "`{}` has no attribute `{}`".format(self.__repr__(), attribute)
        raise AttributeError(msg)

    def _iter_field_attribute_keys(self):
        for attribute_name in self.field_attributes:
            key = attribute_name.replace('_fields', '')
            yield attribute_name, key

    def get_initial(self):
        return self.parsed_data

    def get_usable_fields(self):
        """Returns fields that subclass BindParseValidate
        (and therefor only those which handle input)
        """
        for field in self.fields.values():
            if isinstance(field, base.BindParseValidate):
                yield field

    def iter_fields(self):
        return self.fields.values()

    def get_field_by_input_name(self, input_name):
        """Returns field based on the html name attribute key.

        For MultiValueFields, the key for a subfield, will return the parent
        field
        """
        key_parts = input_name.split('.')
        return self.fields[key_parts.pop(0)]

    def build_field(self, field_class):
        # get init args (required, optional, recommended)
        init_kwargs = dict(form=self)
        for attribute_name, key in self._iter_field_attribute_keys():
            init_kwargs[key] = field_class in getattr(
                self, attribute_name, [])
        init_args = []
        if self.raw_input_data is not base.UNSET:
            init_args.append(self.raw_input_data)
        field = field_class(
            *init_args,
            skip_validation_parse_only=self.skip_validation_parse_only,
            **init_kwargs)
        # this might error if a context_key is not a valid
        # python variable name or if the field is named after
        # an attribute on this object
        setattr(self, field.context_key, field)
        return field

    def _update_field_attributes_with_instances(self):
        """Sets required, optional, and recommended lists of field instances

        For each of `required_fields`, `optional_fields`, and
        `recommended_fields`, this sets the corresponding attribute for each
        to a list of field instances whose relevant attribute (`required`,
        `optional`, `recommended`) is `True`.
        """
        for field_attribute, key in self._iter_field_attribute_keys():
            setattr(self, field_attribute, [
                field for field in self.iter_fields()
                if getattr(field, key, False)
            ])

    def non_field_errors(self):
        return self.get_errors_list()

    def parse(self, raw_value):
        """Should delegate extraction and parsing to fields
            should build up a .parsed_data value and return it
        """
        value = self.empty_value
        for field in self.get_usable_fields():
            field.raw_input_value = field.extract_raw_value(
                field.raw_input_data)
            field.parsed_data = field.parse(field.raw_input_value)
            value[field.context_key] = field.parsed_data
        return value

    def validate(self):
        """Should delegate and bubble up errors from fields
        should then run it's own validators
        """
        for field in self.get_usable_fields():
            # runs validators on fields
            field.validate()
            self.errors.update(field.errors)
            self.warnings.update(field.warnings)
        # runs own validators
        super().validate()

    def is_empty(self):
        """Returns `True` if all subfields are empty
        """
        return all(field.is_empty() for field in self.get_usable_fields())

    def parse_and_validate(self, raw_data):
        super().parse_and_validate(raw_data)
        self.cleaned_data = {
            field.context_key: field.parsed_data
            for field in self.get_usable_fields()
            if field.is_valid()
        }

    def get_template_context(self, context):
        """Add `self` as `form` in render context"""
        context = super().get_template_context(context)
        context['form'] = self
        return context
