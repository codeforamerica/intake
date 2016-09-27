from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from intake.constants import CONTACT_METHOD_CHOICES, CONTACT_PREFERENCE_CHECKS



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


contact_info_json = ContactInfoJSON()
