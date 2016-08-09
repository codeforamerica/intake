from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from intake.constants import CONTACT_METHOD_CHOICES, CONTACT_PREFERENCE_CHECKS
from rest_framework.utils import html


def html_safe_get(obj, key, default=None):
    if html.is_html_input(obj):
        return obj.getlist(key, default)
    return obj.get(key, default)


class GavePreferredContactMethods:
    """Implements the validator protocol of Django REST Framework
        - needs to be callable
        - receives the parent form through the `set_context(form)` method
        - if it finds errors, it should raise a ValidationError to return them
    """
    message_template = _("You said you preferred to be contacted through {medium}, but you didn't enter {datum}.")

    def message(self, preference):
        attributes, medium, datum = CONTACT_PREFERENCE_CHECKS[preference]
        return self.message_template.format(medium=medium, datum=datum)

    def set_context(self, form):
        self.context = form

    def get_field_value(self, field_name, data):
        field = self.context.fields[field_name]
        if hasattr(field, 'fields'):
            value = field.to_internal_value(data.get(field_name, {}))
        else:
            value = data.get(field_name, '')
        return value

    def __call__(self, ignored):
        errors = {}
        data = self.context.get_initial()
        for key in data.get('contact_preferences', []):
            attribute_name, medium, datum = CONTACT_PREFERENCE_CHECKS[key]
            value = self.get_field_value(attribute_name, data)
            has_attribute = bool(value)
            if not has_attribute:
                field_errors = errors.get(attribute_name, [])
                field_errors.append(self.message(key))
                errors[attribute_name] = field_errors
        if errors:
            raise ValidationError(errors)


class ContactInfoJSON:

    NOT_A_DICT = _("ContactInfoJSON must be a dictionary or inherit from it")
    NOT_A_VALID_METHOD = _("'{}' is not a valid contact method")
    NO_VALUE = _("All contact methods should have associated contact info")

    VALID_METHODS = [key for key, verbose in CONTACT_METHOD_CHOICES]


    def should_be_a_dict(self, data):
        if not isinstance(data, dict):
            raise ValidationError(self.NOT_A_DICT)

    def should_be_a_valid_method(self, method):
        if method not in self.VALID_METHODS:
            raise ValidationError(
                self.NOT_A_VALID_METHOD.format(method))

    def should_not_have_an_empty_value(self, value):
        if not value:
            raise ValidationError(self.NO_VALUE)

    def __call__(self, data):
        self.should_be_a_dict(data)
        for method, info in data.items():
            self.should_be_a_valid_method(method)
            self.should_not_have_an_empty_value(info)



gave_preferred_contact_methods = GavePreferredContactMethods()
contact_info_json = ContactInfoJSON()
