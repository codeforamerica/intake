from django.utils.translation import ugettext_lazy as _

CONTACT_METHOD_CHOICES = (
    ('voicemail',  _('voicemail')),
    ('sms',        _('text message')),
    ('email',      _('email')),
    ('snailmail',  _('paper mail')),
)

CONTACT_PREFERENCE_CHOICES = (
    ('prefers_email',     _('Email')),
    ('prefers_sms',       _('Text Message')),
    ('prefers_snailmail', _('Paper mail')),
    ('prefers_voicemail', _('Voicemail')),
    )

CONTACT_PREFERENCE_CHECKS = {
    'prefers_email':     ('email', _('email'), _("an email address")),
    'prefers_sms':       ('phone_number', _('text message'), _("a phone number")),
    'prefers_snailmail': ('address', _('paper mail'), _("a mailing address")),
    'prefers_voicemail': ('phone_number', _('voicemail'), _("a phone number")),
    }

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']

class Counties:
    CONTRA_COSTA = 'contracosta'
    SAN_FRANCISCO = 'sanfrancisco'
    OTHER = 'other'

class CountyNames:
    SAN_FRANCISCO = 'San Francisco'
    CONTRA_COSTA = 'Contra Costa'


COUNTY_CHOICES = (
    (Counties.SAN_FRANCISCO, _('San Francisco')),
    (Counties.CONTRA_COSTA,  _('Conta Costa County (around Richmond, Walnut Creek, Antioch, or Brentwood)')),
    # (Counties.OTHER, _('Some other county'))
    )