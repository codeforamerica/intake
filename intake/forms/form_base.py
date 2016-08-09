from intake.serializer_forms import Form
from intake.forms import fields as F

class CombinableForm:
    """This needs to handle a few things:
    1. [x] it should be able to cleanly combine sets of form fields
        including counties, fields, required_fields and recommended fields
    2. [ ] it should be able to produce a new form instance based on the Django REST API forms.
     that can be used for form processing
    """
    combinable_set_attributes = [
            'counties',
            'fields',
            'required_fields',
            'recommended_fields'
        ]

    def __init__(self, **kwargs):
        for attribute_key in self.combinable_set_attributes:
            init_value = kwargs.get(attribute_key, None)
            if init_value is not None:
                setattr(self, attribute_key, set(init_value))

    def _magic_method_relay(self, other, magic_method):
        """Used to patch magic magic_methods and offload them to internal
        attributes that are builtin `set()` objects. 
        """
        init_kwargs = {}
        for attribute in self.combinable_set_attributes:
            self_set = getattr(self, attribute, set())
            other_set = getattr(other, attribute, set())
            self_set_method = getattr(self_set, magic_method)
            init_kwargs[attribute] = self_set_method(other_set)
        return CombinableForm(**init_kwargs)

    def __or__(self, other):
        return self._magic_method_relay(other, '__or__')

    def __sub__(self, other):
        return self._magic_method_relay(other, '__sub__')

    def get_field_name(self, field):
        """Returns the locals() name for `field` from intake.forms.fields
        """
        for key, thing in F.FIELD_NAME_LOOKUP.items():
            if thing is field:
                return key

    def generate_form_fields(self):
        """Returns a dictionary of class attributes that can 
            be used to build a Form class
            each attribute is assumed to be a field instance

        # go through self.fields and add each field instance
        # to the class_attributes_dictionary
        """
        class_attributes_dictionary = {}
        for field_instance in self.fields:
            attribute_name = self.get_field_name(field_instance)
            class_attributes_dictionary[attribute_name] = field_instance
        return class_attributes_dictionary

    def get_validation_form_class(self):
        # create a new class that inherits from Form
        class_attributes_dictionary = self.generate_form_fields()
        parent_classes_tuple = (Form,)
        return type(
            'ValidatableForm',
            parent_classes_tuple,
            class_attributes_dictionary
            )

    def get_validation_form_instance(self, data=None):
        """Should return an instance of 
            intake.serializer_forms.Form
            that has the correct fields,
            required_fields
        """
        if data is None:
            data = {}
        ValidatableForm = self.get_validation_form_class()
        return ValidatableForm(data)
