from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

CONTACT_PREFERENCE_CHECKS = {
    'prefers_email':     (['email'], _('email'), _("an email address")),
    'prefers_sms':       (['phone_number'], _('text message'), _("a phone number")),
    'prefers_snailmail': (['address_street', 'address_city', 'address_state', 'address_zip'], _('paper mail'), _("a mailing address")),
    'prefers_voicemail': (['phone_number'], _('voicemail'), _("a phone number")),
    }


class GavePreferredContactMethods:
    message_template = _("You said you preferred to be contacted through {medium}, but you didn't enter {datum}.")

    def message(self, preference):
        attributes, medium, datum = CONTACT_PREFERENCE_CHECKS[preference]
        return self.message_template.format(medium=medium, datum=datum)

    def __call__(self, form):
        for key in form.cleaned_data['contact_preferences']:
            has_attributes = False
            attributes, medium, datum = CONTACT_PREFERENCE_CHECKS[key]
            for attribute in attributes:
                if form.cleaned_data.get(attribute, None):
                    has_attributes = True
            if not has_attributes:
                error = ValidationError(self.message(key))
                form.add_error(None, error)


gave_preferred_contact_methods = GavePreferredContactMethods()