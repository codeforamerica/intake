from formation.form_base import Form
from formation.fields import get_field_index


class CombinableFormSpec:

    union_attributes = [
        'fields',
        'required_fields',
        'recommended_fields',
        'validators'
    ]
    difference_attributes = [
        'optional_fields'
    ]
    combinable_attributes = union_attributes + difference_attributes

    def __init__(self, **kwargs):
        for attribute_key in self.combinable_attributes:
            init_value = kwargs.get(attribute_key, None)
            if init_value is not None:
                setattr(self, attribute_key, set(init_value))

    def get_att_sets(self, other, att):
        self_set = getattr(self, att, set())
        other_set = getattr(other, att, set())
        return set(self_set), set(other_set)

    def __or__(self, other):
        """Combines this spec with another spec
        """
        init_kwargs = {}
        for attribute in self.union_attributes:
            self_set, other_set = self.get_att_sets(other, attribute)
            init_kwargs[attribute] = self_set | other_set
        for attribute in self.difference_attributes:
            self_set, other_set = self.get_att_sets(other, attribute)
            self_safe_set = self_set - other.fields
            other_safe_set = other_set - self.fields
            safe_set = self_safe_set | other_safe_set
            in_both = self_set & other_set
            init_kwargs[attribute] = in_both | safe_set
        return self.__class__(**init_kwargs)

    def build_form_class_attributes(self):
        """Returns a dictionary of class attributes
        that are used to create a Form class
        """
        attribute_names = set(self.combinable_attributes.copy())
        attribute_names.remove('fields')
        fields_list = list(self.fields)
        fields_list.sort(key=get_field_index)
        class_attributes = {
            'fields': fields_list}
        for attribute_name in attribute_names:
            value = getattr(self, attribute_name, [])
            if not isinstance(value, list):
                value = list(value)
            class_attributes[attribute_name] = value
        return class_attributes

    def build_form_class(self, extra_class_attributes=None, ParentClass=None):
        """Builds up a CombinedForm class
        """
        class_attributes_dictionary = self.build_form_class_attributes()
        class_attributes_dictionary.update(extra_class_attributes or {})
        if not ParentClass:
            ParentClass = Form
        parent_classes_tuple = (ParentClass,)
        return type(
            'CombinedForm',
            parent_classes_tuple,
            class_attributes_dictionary
        )


class FormSpecSelector:

    def __init__(self, form_specs, form_parent_class=None):
        if form_parent_class is None:
            form_parent_class = Form
        self.form_specs = form_specs
        self.form_parent_class = form_parent_class

    def get_combined_form_spec(self, **criteria):
        combined_spec = None
        specs = filter(
            lambda spec: spec.is_correct_spec(**criteria),
            self.form_specs)
        for spec in specs:
            if combined_spec is None:
                combined_spec = spec
            else:
                combined_spec |= spec
        return combined_spec

    def get_combined_form_class(self, **criteria):
        combined_spec = self.get_combined_form_spec(**criteria)
        return combined_spec.build_form_class(criteria, self.form_parent_class)
