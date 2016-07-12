from django.contrib.postgres.fields import JSONField 
from intake import validators
from rest_framework import serializers


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
        self.label = label
        self.help_text = help_text
        if html_attrs is None:
            html_attrs = {}
        self.html_attrs = html_attrs
        if not kwargs.get('required', True):
            kwargs['allow_blank'] = True
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """This is used to deal with the multiple values in a MultiValueDict
        """
        if not isinstance(data, str) and hasattr(data, '__iter__'):
            return data[0]
        return data

class CharField(SerializerFormField, serializers.CharField):
    pass


class EmailField(SerializerFormField, serializers.EmailField):
    pass


class ChoiceField(SerializerFormField, serializers.ChoiceField):
    pass


class MultipleChoiceField(SerializerFormField, serializers.MultipleChoiceField):
    
    def to_internal_value(self, data):
        return serializers.MultipleChoiceField.to_internal_value(self, data)


