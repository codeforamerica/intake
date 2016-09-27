from django.contrib.postgres.fields import JSONField 
from intake import validators


class ContactInfoJSONField(JSONField):
    """
    A field for storing contact information that validates
    data against expected keys and structure 
    """

    def validate(self, value, model_instance):
        validators.contact_info_json(value)
        super().validate(value, model_instance)

