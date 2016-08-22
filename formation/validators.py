from formation.exceptions import NoChoicesGivenError
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _
from project.jinja2 import oxford_comma
from intake.constants import CONTACT_PREFERENCE_CHECKS


class ValidChoiceValidator:
    """Checks that the input data is a valid choice.
    Calls `.add_error()` on the context with a message
    reporting the invalid input.
    """

    not_found_error = _("{} is not a valid choice.")

    def set_context(self, field):
        if not hasattr(field, 'choices'):
            raise exceptions.NoChoicesGivenError(str(
                "`{}` doesn't have a `choices` attribute.".format(
                    field
                )))
        self.field = field
        self.possible_choices = {
            key: value
            for key, value in field.choices
        }

    def __call__(self, data):
        if data or self.field.required:
            if data not in self.possible_choices:
                self.field.add_error(
                    self.not_found_error.format(data))


class MultipleValidChoiceValidator(ValidChoiceValidator):
    """Checks that each item in the input data is
    a valid choice. Calls `.add_error()` on the context
    with a message reporting which items were invalid.
    """

    multiple_not_found_error = _(
        "{} are not valid choices.")

    def format_error_message(self, missing_values):
        things = ["{}".format(val) for val in missing_values]
        if len(things) == 1:
            fragment = things[0]
            template = self.not_found_error
        else:
            fragment = oxford_comma(things)
            template = self.multiple_not_found_error
        return template.format(fragment)

    def __call__(self, data):
        missing_values = []
        for choice in data:
            if choice not in self.possible_choices:
                missing_values.append(choice)
        if missing_values:
            self.field.add_error(
                self.format_error_message(missing_values))


class GavePreferredContactMethods:
    """Implements the validator protocol of Django REST Framework
        - needs to be callable
        - receives the parent form through the `set_context(form)` method
        - if it finds errors, it should raise a ValidationError to return them
    """
    message_template = _(
        "You said you preferred to be contacted through {medium}, but you didn't enter {datum}.")

    def message(self, preference):
        attributes, medium, datum = CONTACT_PREFERENCE_CHECKS[preference]
        return self.message_template.format(medium=medium, datum=datum)

    def set_context(self, form):
        self.context = form

    def field_is_empty(self, field_name):
        field = getattr(self.context, field_name)
        return field.is_empty()

    def __call__(self, parsed_data):
        errors = {}
        for key in parsed_data.get('contact_preferences', []):
            attribute_name, medium, datum = CONTACT_PREFERENCE_CHECKS[key]
            if self.field_is_empty(attribute_name):
                field_errors = errors.get(attribute_name, [])
                field_errors.append(self.message(key))
                errors[attribute_name] = field_errors
        if errors:
            raise ValidationError(errors)

is_a_valid_choice = ValidChoiceValidator()
are_valid_choices = MultipleValidChoiceValidator()
gave_preferred_contact_methods = GavePreferredContactMethods()
