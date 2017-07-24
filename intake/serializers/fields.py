import datetime
from rest_framework import serializers
from intake.constants import PACIFIC_TIME

from formation.display_form_base import DisplayForm
from django.utils.safestring import mark_safe
from formation import fields as F

THIS_YEAR = datetime.datetime.now().year


class ContactInfoMiniForm(DisplayForm):
    fields = [
        F.PhoneNumberField,
        F.AlternatePhoneNumberField,
        F.AddressField,
        F.EmailField,
    ]


class ContactInfoByPreferenceField(serializers.Field):
    """A read only field that pulls out salient contact
        information for display.
    """

    def to_representation(self, obj):
        mini_form = ContactInfoMiniForm(obj)
        contact_preferences = obj.get('contact_preferences', [])
        output = []
        for key in ('sms', 'email', 'voicemail', 'snailmail'):
            pref = 'prefers_' + key
            if pref in contact_preferences:
                if key == 'email':
                    output.append((
                        key, mark_safe(
                            mini_form.email.get_display_value())
                    ))
                elif key == 'snailmail':
                    output.append((
                        key, mark_safe(
                            mini_form.address.get_inline_display_value())
                    ))
                elif key in ('sms', 'voicemail'):
                    output.append((
                        key, mark_safe(
                            mini_form.phone_number.get_display_value())
                    ))
        return output


class LocalDateField(serializers.DateTimeField):

    def __init__(self, *args, tz=PACIFIC_TIME, **kwargs):
        super().__init__(*args, **kwargs)
        self.tz = tz

    def to_representation(self, dt):
        return dt.astimezone(self.tz)


class FormattedLocalDateField(LocalDateField):

    def __init__(self, *args, format="%m/%d/%Y", **kwargs):
        super().__init__(*args, **kwargs)
        self.format = format

    def to_representation(self, dt):
        return super().to_representation(dt).strftime(self.format)


class ChainableAttributeField(serializers.Field):

    def __init__(self, attribute_accessor_sequence, *args, **kwargs):
        kwargs['source'] = kwargs.pop('source', '*')
        super().__init__(*args, **kwargs)
        self.attribute_accessor_sequence = attribute_accessor_sequence

    def to_representation(self, obj):
        value = obj
        attribute_sequence = getattr(
            self, 'attribute_accessor_sequence', '').split('.')
        while attribute_sequence:
            accessor = attribute_sequence.pop(0)
            if accessor:
                value = getattr(value, accessor)
        return value
