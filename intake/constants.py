from django.utils.translation import ugettext as _

CONTACT_METHOD_CHOICES = (
    ('voicemail',  _('voicemail')),
    ('sms',        _('text message')),
    ('email',      _('email')),
    ('snailmail',  _('paper mail')),
)

CONTACT_PREFERENCE_CHECKS = {
    'prefers_email':     (['email'], _('email'), _("an email address")),
    'prefers_sms':       (['phone_number'], _('text message'), _("a phone number")),
    'prefers_snailmail': (['address_street', 'address_city', 'address_state', 'address_zip'], _('paper mail'), _("a mailing address")),
    'prefers_voicemail': (['phone_number'], _('voicemail'), _("a phone number")),
    }

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']