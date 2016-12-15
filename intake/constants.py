from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from pytz import timezone

PACIFIC_TIME = timezone('US/Pacific')

SCOPE_TO_LIVE_COUNTIES = getattr(settings, 'LIVE_COUNTY_CHOICES', False)

# Communication methods
SMS = 'sms'
EMAIL = 'email'
VOICEMAIL = 'voicemail'
SNAILMAIL = 'snailmail'

CONTACT_METHOD_CHOICES = (
    (VOICEMAIL, _(VOICEMAIL)),
    (SMS, _('text message')),
    (EMAIL, _(EMAIL)),
    (SNAILMAIL, _('paper mail')),
)

CONTACT_PREFERENCE_CHOICES = (
    ('prefers_email', _('Email')),
    ('prefers_sms', _('Text Message')),
    ('prefers_snailmail', _('Paper mail')),
    ('prefers_voicemail', _('Voicemail')),
)

CONTACT_PREFERENCE_CHECKS = {
    'prefers_email': (EMAIL, _(EMAIL), _("an email address")),
    'prefers_sms': ('phone_number', _('text message'), _("a phone number")),
    'prefers_snailmail': ('address', _('paper mail'), _("a mailing address")),
    'prefers_voicemail': ('phone_number', _(VOICEMAIL), _("a phone number")),
}

GENDER_PRONOUN_CHOICES = (
    ('he', _('He/Him/His')),
    ('she', _('She/Her/Hers')),
    ('they', _('They/Them/Their')),
    ('none', _('Prefer not to answer')),
)

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']


class Organizations:
    CFA = 'cfa'
    SF_PUBDEF = 'sf_pubdef'
    COCO_PUBDEF = 'cc_pubdef'
    ALAMEDA_PUBDEF = 'a_pubdef'
    MONTEREY_PUBDEF = 'monterey_pubdef'
    EBCLC = 'ebclc'
    ALL = 'all'

DEFAULT_ORGANIZATION_ORDER = [
    Organizations.ALL,
    Organizations.SF_PUBDEF,
    Organizations.ALAMEDA_PUBDEF,
    Organizations.EBCLC,
    Organizations.COCO_PUBDEF,
    Organizations.MONTEREY_PUBDEF,
]


ORG_NAMES = {
    Organizations.CFA: _("Code for America"),
    Organizations.SF_PUBDEF: _("San Francisco Public Defender"),
    Organizations.COCO_PUBDEF: _("Contra Costa Public Defender"),
    Organizations.ALAMEDA_PUBDEF: _("Alameda County Public Defender's Office"),
    Organizations.MONTEREY_PUBDEF: _("Monterey County Public Defender"),
    Organizations.EBCLC: _("East Bay Community Law Center"),
}

PAGE_COMPLETE_SEQUENCES = {
    Organizations.SF_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.COCO_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.ALAMEDA_PUBDEF: [
        "SelectCounty", "CountyApplication",
        "DeclarationLetterView", "DeclarationLetterReviewPage"],
    Organizations.MONTEREY_PUBDEF: [
        "SelectCounty", "CountyApplication",
        "DeclarationLetterView", "DeclarationLetterReviewPage"],
    Organizations.EBCLC: ["SelectCounty", "CountyApplication"],
}


class Counties:
    CONTRA_COSTA = 'contracosta'
    SAN_FRANCISCO = 'sanfrancisco'
    ALAMEDA = 'alameda'
    MONTEREY = 'monterey'
    OTHER = 'other'


class CountyNames:
    SAN_FRANCISCO = 'San Francisco'
    CONTRA_COSTA = 'Contra Costa'
    ALAMEDA = 'Alameda'
    MONTEREY = 'Monterey'
    ALL = 'San Francisco, Alameda, Contra Costa, and Monterey Counties'


if SCOPE_TO_LIVE_COUNTIES:
    CountyNames.ALL = 'San Francisco, Alameda, and Contra Costa Counties'


if SCOPE_TO_LIVE_COUNTIES:
    COUNTY_CHOICES = (
        (Counties.SAN_FRANCISCO, _('San Francisco')),
        (Counties.CONTRA_COSTA, _(
            'Conta Costa County (near Richmond, Concord, Walnut Creek, '
            'San Ramon, Antioch, or Brentwood)')),
        (Counties.ALAMEDA, _(
            'Alameda County (near Oakland, Berkeley, San Leandro, Hayward, '
            'Fremont, Albany, Newark, Dublin, Union City, Pleasanton, '
            'or Livermore)')),
        # (Counties.MONTEREY, _(
        #     'Monterey County (near Salinas, Monterey, Marina, Seaside, '
        #     'Prunedale, Castroville, or King City)')),
    )
else:
    COUNTY_CHOICES = (
        (Counties.SAN_FRANCISCO, _('San Francisco')),
        (Counties.CONTRA_COSTA, _(
            'Conta Costa County (near Richmond, Concord, Walnut Creek, '
            'San Ramon, Antioch, or Brentwood)')),
        (Counties.ALAMEDA, _(
            'Alameda County (near Oakland, Berkeley, San Leandro, Hayward, '
            'Fremont, Albany, Newark, Dublin, Union City, Pleasanton, '
            'or Livermore)')),
        (Counties.MONTEREY, _(
            'Monterey County (near Salinas, Monterey, Marina, Seaside, '
            'Prunedale, Castroville, or King City)')),
    )

COUNTY_CHOICE_DISPLAY_DICT = {
    Counties.SAN_FRANCISCO: CountyNames.SAN_FRANCISCO,
    Counties.CONTRA_COSTA: CountyNames.CONTRA_COSTA,
    Counties.ALAMEDA: CountyNames.ALAMEDA,
    Counties.MONTEREY: CountyNames.MONTEREY,
}


FEE_WAIVER_LEVELS = {
    1: 16395,
    2: 22108,
    3: 27821,
    4: 33534,
    5: 39248,
    6: 44962,
    7: 50688,
    8: 56429,
    9: 62169,
    10: 67910,
    11: 73651,
    12: 79392,
}
