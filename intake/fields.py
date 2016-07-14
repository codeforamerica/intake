from django.contrib.postgres.fields import JSONField 
from intake import validators
import rest_framework
from rest_framework import serializers

from django.utils.translation import ugettext as _


YES_NO_CHOICES = (
    ('yes', _('Yes')),
    ('no',  _('No')),
    )

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


class FormField(serializers.Field):
    """A serializer field that adds some additional convenience attributes
        for rendering as an HTML form and mimicking parts of the Django
        FormField API
    """
    label = None
    help_text = ""
    html_attrs = {}

    def __init__(self, *args, **kwargs):
        self.add_default_init_args(kwargs)
        super().__init__(*args, **kwargs)
        self.label = kwargs.get('label', self.label)
        self.help_text = kwargs.get('help_text', self.help_text)
        self.html_attrs.update(kwargs.get('html_attrs', {}))

    def add_default_init_args(self, kwargs):
        """Allows FormField classes to set class attributes
            that are passed to the parent class __init__ method
            in order to be used as instance attributes.
            In other words, add_default_init_args allows subclasses
            to set class attributes that are used as default values
            for instance attributes.
        """
        inheritable_args = ['required']
        for key in inheritable_args:
            if key not in kwargs and hasattr(self, key):
                kwargs[key] = getattr(self, key)


    def get_value(self, dictionary):
        value = super().get_value(dictionary)
        return self.coerce_if_empty(value)

    def get_empty_value(self):
        """Gets the default value for empty versions of this field
            Often overridden in subclasses in order to provide different types of empty
            values
        """
        return ""

    def field_errors(self):
        """Returns any errors from a parent field or form that pertain to this field
        """
        if hasattr(self, 'parent'):
            parent = self.parent
            if hasattr(parent, '_errors'):
                return parent.errors.get(self.field_name, [])
        return []

    def field_warnings(self):
        """Returns any warnings from a parent field or form that pertain to this field
        """
        if hasattr(self, 'parent'):
            parent = self.parent
            if hasattr(parent, 'warnings'):
                return parent.warnings.get(self.field_name, [])
        return []

    def coerce_if_empty(self, value):
        """Coerces empty values to the default empty value for this field
        """
        if value == rest_framework.fields.empty:
            return self.get_empty_value()
        return value

    def current_value(self):
        """Returns the current value for this field
        More research into Django REST Framework
        might simplify or obviate this method
        """
        if hasattr(self, 'parent'):
            base_data = getattr(self.parent, 'initial_data', self.parent.get_initial())
            if hasattr(self, 'fields'):
                base_value = self.get_value(base_data)
                value = self.to_internal_value(base_value)
            elif isinstance(self.parent, FormField):
                value = getattr(self.parent.current_value(), self.field_name)
            else:
                value = self.get_value(base_data)
            return self.coerce_if_empty(value)

    def input_name(self):
        """Returns a string for use as an html input name value
        """
        if hasattr(self, 'parent'):
            if getattr(self.parent, 'field_name', ''):
                return "{}.{}".format(self.parent.field_name, self.field_name)
        return self.field_name

    def class_name(self):
        return self.input_name().replace('.', '_')


class BlankIfNotRequiredField(FormField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('required', getattr(self, 'required', True)):
            kwargs['allow_blank'] = True
        super().__init__(*args, **kwargs)


class CharField(BlankIfNotRequiredField, serializers.CharField):
    pass


class EmailField(BlankIfNotRequiredField, serializers.EmailField):
    pass


class ChoiceField(BlankIfNotRequiredField, serializers.ChoiceField):
    choices = None
    def __init__(self, *args, **kwargs):
        choices = kwargs.get('choices', None)
        if not choices and hasattr(self, 'choices'):
            choices = getattr(self, 'choices')
        if not choices:
            raise TypeError("'choices' is a required attribute. It must be provided or passed to __init__.")
        super().__init__(choices, *args, **kwargs)


class YesNoBlankField(ChoiceField):
    choices = YES_NO_CHOICES
    required = False


class MultipleChoiceField(FormField, serializers.MultipleChoiceField):
    def to_internal_value(self, data):
        return serializers.MultipleChoiceField.to_internal_value(self, data)

    def to_representation(self, obj):
        return list(obj)

    def get_empty_value(self):
        return []


class MultiValueFormField(serializers.Serializer, FormField):

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


class AddressMultiValueFormField(MultiValueFormField):
    label = _("What is your mailing address?")
    help_text = _("The public defender will need to send you important papers.")

    street = CharField(required=False)
    city = CharField(label=_("City"), required=False)
    state = CharField(label=_("State"), required=False)
    zip = CharField(label=_("Zip"), required=False)

    def build_instance(self, **kwargs):
        return Address(**kwargs)


class DateOfBirthMultiValueFormField(MultiValueFormField):
    label = _("What is your date of birth?")
    help_text = _("For example: 4/28/1986")

    month = CharField(label=_("Month"), required=False)
    day = CharField(label=_("Day"), required=False)
    year = CharField(label=_("Year"), required=False)

    def build_instance(self, **kwargs):
        return DateOfBirth(**kwargs)
