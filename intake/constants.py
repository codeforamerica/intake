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

REASON_FOR_APPLYING_CHOICES = (
    ('background_check', _('To pass a background check')),
    ('pending_job', _('I have a job offer pending')),
    ('housing', _('To qualify for housing')),
    ('immigration', _('Immigration status issues')),
    ('lost_job', _('Was asked to leave job because of my record')),
    ('early_probation', _('End probation early')),
    ('homeless', _('Homeless or on social services')),
    ('other', _('My reason is not listed')),
)

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']


class Organizations:
    ALL = 'all'
    CFA = 'cfa'
    SF_PUBDEF = 'sf_pubdef'
    COCO_PUBDEF = 'cc_pubdef'
    ALAMEDA_PUBDEF = 'a_pubdef'
    MONTEREY_PUBDEF = 'monterey_pubdef'
    EBCLC = 'ebclc'
    SOLANO_PUBDEF = 'solano_pubdef'
    SAN_DIEGO_PUBDEF = 'san_diego_pubdef'
    SAN_JOAQUIN_PUBDEF = 'san_joaquin_pubdef'
    SANTA_CLARA_PUBDEF = 'santa_clara_pubdef'
    FRESNO_PUBDEF = 'fresno_pubdef'

DEFAULT_ORGANIZATION_ORDER = [
    Organizations.ALL,
    Organizations.SF_PUBDEF,
    Organizations.ALAMEDA_PUBDEF,
    Organizations.EBCLC,
    Organizations.COCO_PUBDEF,
    Organizations.MONTEREY_PUBDEF,
    Organizations.SOLANO_PUBDEF,
    Organizations.SAN_DIEGO_PUBDEF,
    Organizations.SAN_JOAQUIN_PUBDEF,
    Organizations.SANTA_CLARA_PUBDEF,
    Organizations.FRESNO_PUBDEF,
]


ORG_NAMES = {
    Organizations.CFA: _("Code for America"),
    Organizations.SF_PUBDEF: _("San Francisco Public Defender"),
    Organizations.COCO_PUBDEF: _("Contra Costa Public Defender"),
    Organizations.ALAMEDA_PUBDEF: _("Alameda County Public Defender's Office"),
    Organizations.MONTEREY_PUBDEF: _("Monterey County Public Defender"),
    Organizations.EBCLC: _("East Bay Community Law Center"),
    Organizations.SOLANO_PUBDEF: _("Solano County Public Defender"),
    Organizations.SAN_DIEGO_PUBDEF: _("San Diego County Public Defender"),
    Organizations.SAN_JOAQUIN_PUBDEF: _("San Joaquin County Public Defender"),
    Organizations.SANTA_CLARA_PUBDEF: _("Santa Clara County Public Defender"),
    Organizations.FRESNO_PUBDEF: _("Fresno County Public Defender"),
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
    Organizations.SOLANO_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SAN_DIEGO_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SAN_JOAQUIN_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SANTA_CLARA_PUBDEF: [
        "SelectCounty", "CountyApplication",
        "DeclarationLetterView", "DeclarationLetterReviewPage"],
    Organizations.FRESNO_PUBDEF: ["SelectCounty", "CountyApplication"],
}


class Counties:
    CONTRA_COSTA = 'contracosta'
    SAN_FRANCISCO = 'sanfrancisco'
    ALAMEDA = 'alameda'
    MONTEREY = 'monterey'
    SOLANO = 'solano'
    SAN_DIEGO = 'san_diego'
    SAN_JOAQUIN = 'san_joaquin'
    SANTA_CLARA = 'santa_clara'
    FRESNO = 'fresno'
    OTHER = 'other'


class CountyNames:
    SAN_FRANCISCO = 'San Francisco'
    CONTRA_COSTA = 'Contra Costa'
    ALAMEDA = 'Alameda'
    MONTEREY = 'Monterey'
    SOLANO = 'Solano'
    SAN_DIEGO = 'San Diego'
    SAN_JOAQUIN = 'San Joaquin'
    SANTA_CLARA = 'Santa Clara'
    FRESNO = 'Fresno'
    ALL = 'counties throughout California'


if SCOPE_TO_LIVE_COUNTIES:
    CountyNames.ALL = str(
        'San Francisco, Alameda, Contra Costa, and Monterey Counties')


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
    (Counties.FRESNO, _(
        'Fresno County (near Fresno, Clovis, Sanger, Kingsburg, Mendota, '
        'Fowler, or Three Rocks)')),
)
if not SCOPE_TO_LIVE_COUNTIES:
    COUNTY_CHOICES += (
        (Counties.SOLANO, _(
            'Solano County (near Vallejo, Fairfield, Vacaville, Benicia, '
            'or Allendale)')),
        (Counties.SAN_DIEGO, _(
            'San Diego County (near San Diego, Oceanside, Chula Vista, or '
            'Escondido)')),
        (Counties.SAN_JOAQUIN, _(
            'San Joaquin County (near Lodi, Stockton, Tracy, Manteca, '
            'Thornton, or Victor)')),
        (Counties.SANTA_CLARA, _(
            'Santa Clara County (near San Jose, Santa Clara, Campbell, '
            'Saratoga, Los Altos, Los Gatos, or Gilroy)')),
    )

COUNTY_CHOICES = sorted(COUNTY_CHOICES, key=lambda item: item[1])

COUNTY_CHOICE_DISPLAY_DICT = {
    Counties.SAN_FRANCISCO: CountyNames.SAN_FRANCISCO,
    Counties.CONTRA_COSTA: CountyNames.CONTRA_COSTA,
    Counties.ALAMEDA: CountyNames.ALAMEDA,
    Counties.MONTEREY: CountyNames.MONTEREY,
    Counties.SOLANO: CountyNames.SOLANO,
    Counties.SAN_DIEGO: CountyNames.SAN_DIEGO,
    Counties.SAN_JOAQUIN: CountyNames.SAN_JOAQUIN,
    Counties.SANTA_CLARA: CountyNames.SANTA_CLARA,
    Counties.FRESNO: CountyNames.FRESNO,
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
