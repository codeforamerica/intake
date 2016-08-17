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

    def __init__(self, *args, files=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = OrderedDict([
            (field_class.context_key, self.build_field(field_class))
            for field_class in self.fields])
        self.empty_value = {
            field.context_key: field.empty_value
            for field in self.get_usable_fields()}
        self.cleaned_data = base.UNSET

    @classmethod
    def get_field_keys(cls):
        for field_class in cls.fields:
            yield field_class.context_key

    def get_initial(self):
        return self.parsed_data

    def get_usable_fields(self):
        for field in self.fields.values():
            if isinstance(field, base.BindParseValidate):
                yield field

    def iter_fields(self):
        return self.fields.values()

    def build_field(self, field_class):
        # get init args (required, optional, recommended)
        init_kwargs = dict(form=self)
        for attribute_name in self.field_attributes:
            arg_key = attribute_name.replace('_fields', '')
            init_kwargs[arg_key] = field_class in getattr(self, attribute_name, [])
        init_args = []
        if self.raw_input_data is not base.UNSET:
            init_args.append(self.raw_input_data)
        field = field_class(*init_args, **init_kwargs)
        # replace class with instance in attributes
        for att_name in self.field_attributes:
            field_attribute = getattr(self, att_name, [])
            if field_class in field_attribute:
                index = field_attribute.index(field_class)
                field_attribute[index] = field
        # this might error if a context_key is not a valid
        # python variable name or if the field is named after
        # an attribute on this object
        setattr(self, field.context_key, field)
        return field

    def non_field_errors(self):
        return self.get_errors_list()

    def parse(self, raw_value):
        """Should delegate extraction and parsing to fields
            should build up a .parsed_data value and return it
        """
        value = self.empty_value
        for field in self.get_usable_fields():
            field.raw_input_value = field.extract_raw_value(field.raw_input_data)
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
    
