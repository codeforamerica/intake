from django.contrib.postgres.fields import JSONField 
from intake import validators
import rest_framework
from rest_framework import serializers

from django.utils.translation import ugettext as _


class FalseIfHasEmptyValue:
    def __bool__(self):
        return all(vars(self).values())

    def __repr__(self):
        fields = sorted(vars(self).keys())
        field_strs = ["{}='{}'".format(f, getattr(self, f)) for f in fields]
        return '<{}({})>'.format(self.__class__.__name__, ', '.join(field_strs))

    def __eq__(self, other):
        return vars(self) == vars(other)


class Address(FalseIfHasEmptyValue):
    def __init__(self, street='', city='', state='', zip=''):
        self.street = street
        self.city = city
        self.state = state
        self.zip = zip


class DateOfBirth(FalseIfHasEmptyValue):
    def __init__(self, month='', day='', year=''):
        self.month = month
        self.day = day
        self.year = year


class ContactInfoJSONField(JSONField):
    """
    A field for storing contact information that validates
    data against expected keys and structure 
    """

    def validate(self, value, model_instance):
        validators.contact_info_json(value)
        super().validate(value, model_instance)


class SerializerFormField(serializers.Field):
    """A serializer field that adds some additional convenience attributes
        for rendering as an HTML form and mimicking parts of the Django
        FormField API
    """
    def __init__(self, label=None, help_text="", html_attrs=None, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.help_text = help_text
        if html_attrs is None:
            html_attrs = {}
        self.html_attrs = html_attrs

    def get_value(self, dictionary):
        value = super().get_value(dictionary)
        return self.coerce_if_empty(value)

    def get_empty_value(self):
        return ""

    def field_errors(self):
        if hasattr(self, 'parent'):
            parent = self.parent
            if hasattr(parent, '_errors'):
                return parent.errors.get(self.field_name, [])
        return []

    def field_warnings(self):
        if hasattr(self, 'parent'):
            parent = self.parent
            if hasattr(parent, 'warnings'):
                return parent.warnings.get(self.field_name, [])
        return []

    def coerce_if_empty(self, value):
        if value == rest_framework.fields.empty:
            return self.get_empty_value()
        return value

    def current_value(self):
        if hasattr(self, 'parent'):
            base_data = getattr(self.parent, 'initial_data', self.parent.get_initial())
            if hasattr(self, 'fields'):
                base_value = self.get_value(base_data)
                value = self.to_internal_value(base_value)
            elif isinstance(self.parent, SerializerFormField):
                value = getattr(self.parent.current_value(), self.field_name)
            else:
                value = self.get_value(base_data)
            return self.coerce_if_empty(value)

    def input_name(self):
        if hasattr(self, 'parent'):
            if hasattr(self.parent, 'field_name'):
                return "{}.{}".format(self.parent.field_name, self.field_name)
        return self.field_name


class BlankIfNotRequiredField(SerializerFormField):
    def __init__(self, **kwargs):
        if not kwargs.get('required', True):
            kwargs['allow_blank'] = True
        super().__init__(**kwargs)


class CharField(BlankIfNotRequiredField, serializers.CharField):
    pass

class EmailField(BlankIfNotRequiredField, serializers.EmailField):
    pass


class ChoiceField(BlankIfNotRequiredField, serializers.ChoiceField):
    pass


class MultipleChoiceField(SerializerFormField, serializers.MultipleChoiceField):
    def to_internal_value(self, data):
        return serializers.MultipleChoiceField.to_internal_value(self, data)

    def to_representation(self, obj):
        return list(obj)

    def get_empty_value(self):
        return []


class MultiValueField(serializers.Serializer, SerializerFormField):

    def to_internal_value(self, data):
        base_data = super().to_internal_value(data)
        kwargs = {}
        for key in self.fields:
            kwargs[key] = base_data.get(key, "").strip()
        # just need something that gives
        return self.build_instance(**kwargs)

    def get_empty_value(self):
        return self.build_instance()

    def to_representation(self, obj):
        return vars(obj)

    def get_value(self, dictionary):
        value = super().get_value(dictionary)
        if value == rest_framework.fields.empty:
            return {}
        return value


class AddressFieldSerializer(MultiValueField):
    street = CharField(required=False)
    city = CharField(label=_("City"), required=False)
    state = CharField(label=_("State"), required=False)
    zip = CharField(label=_("Zip"), required=False)

    def build_instance(self, **kwargs):
        return Address(**kwargs)


class DateOfBirthFieldSerializer(MultiValueField):
    month = CharField(label=_("Month"), required=False)
    day = CharField(label=_("Day"), required=False)
    year = CharField(label=_("Year"), required=False)

    def build_instance(self, **kwargs):
        return DateOfBirth(**kwargs)



