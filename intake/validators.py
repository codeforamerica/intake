from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from intake.constants import CONTACT_METHOD_CHOICES
from intake import utils
from intake import example_contexts
from jinja2.exceptions import TemplateError


@deconstructible
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


@deconstructible
class TemplateFieldValidator:
    """Ensure that a template string will compile and render
    """

    def validate_no_unrendered_variables(self, result):
        if '{' in result or '}' in result:
            self.errors.append(
                ValidationError(
                    '\n'.join([
                        'There are curly brackets in the rendered result:',
                        result])))

    def validate_render_with_example_data(self, template):
        """Tests rendering the compiled template with example contexts
        """
        self.errors = []
        try:
            result = template.render(
                example_contexts.status_notification_context())
            self.validate_no_unrendered_variables(result)
        except Exception as error:
            self.errors.append(
                ValidationError(
                    "Could not render this template with an example context"))
            self.errors.append(ValidationError(error))
        from user_accounts.models import Organization
        for org in Organization.objects.filter(is_receiving_agency=True):
            try:
                result = template.render(
                    example_contexts.status_notification_context(
                        organization=org))
                self.validate_no_unrendered_variables(result)
            except Exception as error:
                self.errors.append(
                    ValidationError(
                        "Could not render this template with {}".format(
                            org.name)))
                self.errors.append(ValidationError(error))

    def check_compilation(self, data):
        """Tests that a template string can be successfully compiled
        """
        exception = None
        result = None
        try:
            result = utils.compile_template_string(data)
        except TemplateError as error:
            exception = error
        return result, exception

    def __call__(self, data):
        compilation_result, compilation_exception = \
            self.check_compilation(data)
        if compilation_exception:
            raise ValidationError([
                ValidationError("This template failed to compile"),
                ValidationError(compilation_exception)
            ])
        self.validate_render_with_example_data(compilation_result)
        if self.errors:
            raise ValidationError(self.errors)


contact_info_json = ContactInfoJSON()
template_field_renders_correctly = TemplateFieldValidator()
