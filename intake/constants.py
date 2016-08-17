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

GENDER_PRONOUN_CHOICES = (
    ('he',   _('He/Him/His')),
    ('she',  _('She/Her/Hers')),
    ('they', _('They/Them/Theirs')),
    ('none', _('Prefer not to answer')),
    )

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']

class Counties:
    CONTRA_COSTA = 'contracosta'
    SAN_FRANCISCO = 'sanfrancisco'
    ALAMEDA = 'alameda'
    OTHER = 'other'

class CountyNames:
    SAN_FRANCISCO = 'San Francisco'
    CONTRA_COSTA = 'Contra Costa'
    ALAMEDA = 'Alameda'
    ALL = 'San Francisco, Alameda, and Contra Costa Counties'

CONFIRMATION_MESSAGES = {
    Counties.SAN_FRANCISCO: _("You will get a letter in the mail from the San Francisco Public Defender in 2-4 weeks."),
    Counties.CONTRA_COSTA: _("The Contra Costa Public Defender will follow up with you if they need any other information."),
    Counties.ALAMEDA: _("In # weeks, you will get a phone call from the Alameda Public Defender with an update on your case.")
    }


COUNTY_CHOICES = (
    (Counties.SAN_FRANCISCO, _('San Francisco')),
    (Counties.CONTRA_COSTA,  _('Conta Costa County (near Richmond, Walnut Creek, Antioch, or Brentwood)')),
    (Counties.ALAMEDA,  _('Alameda County (near Oakland, Berkeley, San Leandro, Hayward, Union City, Pleasanton, or Livermore)')),
    # (Counties.OTHER, _('Some other county'))
    )

COUNTY_CHOICE_DISPLAY_DICT = {
    Counties.SAN_FRANCISCO: CountyNames.SAN_FRANCISCO,
    Counties.CONTRA_COSTA: CountyNames.CONTRA_COSTA,
    Counties.ALAMEDA: CountyNames.ALAMEDA,
}

