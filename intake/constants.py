from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from pytz import timezone

PACIFIC_TIME = timezone('US/Pacific')
LANGUAGES_LOOKUP = dict(settings.LANGUAGES)

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
    ('new_case', _('I have a new case pending')),
    ('other', _('My reason is not listed')),
)

APPROVE_LETTER = 'approve_letter'
EDIT_LETTER = 'edit_letter'

DECLARATION_LETTER_REVIEW_CHOICES = (
    (EDIT_LETTER, _('Edit letter')),
    (APPROVE_LETTER, _('Approve letter')),
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
    SANTA_CRUZ_PUBDEF = 'santa_cruz_pubdef'
    SONOMA_PUBDEF = 'sonoma_pubdef'
    TULARE_PUBDEF = 'tulare_pubdef'
    VENTURA_PUBDEF = 'ventura_pubdef'
    SANTA_BARBARA_PUBDEF = 'santa_barbara_pubdef'
    YOLO_PUBDEF = 'yolo_pubdef'
    STANISLAUS_PUBDEF = 'stanislaus_pubdef'

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
    Organizations.SANTA_CRUZ_PUBDEF,
    Organizations.FRESNO_PUBDEF,
    Organizations.SONOMA_PUBDEF,
    Organizations.TULARE_PUBDEF,
    Organizations.VENTURA_PUBDEF,
    Organizations.SANTA_BARBARA_PUBDEF,
    Organizations.YOLO_PUBDEF,
    Organizations.STANISLAUS_PUBDEF,
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
    Organizations.SANTA_CRUZ_PUBDEF: _("Santa Cruz County Public Defender"),
    Organizations.FRESNO_PUBDEF: _("Fresno County Public Defender"),
    Organizations.SONOMA_PUBDEF: _("Sonoma County Public Defender"),
    Organizations.TULARE_PUBDEF: _("Tulare County Public Defender"),
    Organizations.VENTURA_PUBDEF: _("Ventura County Public Defender"),
    Organizations.SANTA_BARBARA_PUBDEF: _(
        "Santa Barbara County Public Defender"),
    Organizations.YOLO_PUBDEF: _("Yolo County Public Defender"),
    Organizations.STANISLAUS_PUBDEF: _("Stanislaus County Public Defender"),
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
    Organizations.SANTA_CRUZ_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SANTA_CLARA_PUBDEF: [
        "SelectCounty", "CountyApplication",
        "DeclarationLetterView", "DeclarationLetterReviewPage"],
    Organizations.FRESNO_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SONOMA_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.TULARE_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.VENTURA_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.SANTA_BARBARA_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.YOLO_PUBDEF: ["SelectCounty", "CountyApplication"],
    Organizations.STANISLAUS_PUBDEF: ["SelectCounty", "CountyApplication"],
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
    SANTA_CRUZ = 'santa_cruz'
    FRESNO = 'fresno'
    SONOMA = 'sonoma'
    TULARE = 'tulare'
    VENTURA = 'ventura'
    SANTA_BARBARA = 'santa_barbara'
    YOLO = 'yolo'
    STANISLAUS = 'stanislaus'
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
    SANTA_CRUZ = 'Santa Cruz'
    FRESNO = 'Fresno'
    SONOMA = 'Sonoma'
    TULARE = 'Tulare'
    VENTURA = 'Ventura'
    SANTA_BARBARA = 'Santa Barbara'
    YOLO = 'Yolo'
    STANISLAUS = 'Stanislaus'
    ALL = 'counties throughout California'


COUNTY_CHOICES = (
    (Counties.SAN_FRANCISCO, _('San Francisco')),
    (Counties.CONTRA_COSTA, _(
        'Contra Costa County (near Richmond, Concord, Walnut Creek, '
        'San Ramon, Antioch, or Brentwood)')),
    (Counties.ALAMEDA, _(
        'Alameda County (near Oakland, Berkeley, San Leandro, Hayward, '
        'Fremont, Albany, Newark, Dublin, Union City, Pleasanton, '
        'or Livermore)')),
    (Counties.FRESNO, _(
        'Fresno County (near Fresno, Clovis, Sanger, Kingsburg, Mendota, '
        'Fowler, Selma, Coalinga, Orange Cove, Reedley, Huron, Kerman)')),
    (Counties.SOLANO, _(
        'Solano County (near Vallejo, Fairfield, Vacaville, Benicia, '
        'Dixon, Rio Vista, or Suisun City)')),
    (Counties.SANTA_CRUZ, _(
        'Santa Cruz County (near Santa Cruz, Watsonville, Capitola, '
        'Felton, Scotts Valley, Aptos, or Boulder Creek)')),
    (Counties.SAN_DIEGO, _(
        'San Diego County (near San Diego, Oceanside, Chula Vista, or '
        'El Cajon)')),
    (Counties.SANTA_CLARA, _(
        'Santa Clara County (near San Jose, Santa Clara, Campbell, Los '
        'Altos, Los Gatos, Palo Alto, Mountain View, Sunnyvale, Morgan '
        'View, or Gilroy)')),
    (Counties.SONOMA, _(
            'Sonoma County (near Santa Rosa, Petaluma, Sonoma, '
            'Sebastopol, Bodega Bay, Healdsburg, or Cloverdale)')),
    (Counties.SANTA_BARBARA, _(
        'Santa Barbara County (near Santa Maria, Santa Barbara, Goleta, '
        'Carpinteria, Solvang, and Lompoc)'))
)

if SCOPE_TO_LIVE_COUNTIES and len(COUNTY_CHOICES) == 3:
    CountyNames.ALL = str(
        'San Francisco, Alameda, and Contra Costa Counties')

if not SCOPE_TO_LIVE_COUNTIES:
    COUNTY_CHOICES += (
        (Counties.SAN_JOAQUIN, _(
            'San Joaquin County (near Stockton, Lodi, Tracy, Manteca, Ripon, '
            'Escalon, Lathrop, or Thornton)')),
        (Counties.MONTEREY, _(
            'Monterey County (near Salinas, Monterey, Marina, Seaside, '
            'Prunedale, Castroville, or King City)')),
        (Counties.TULARE, _(
            'Tulare County (near Visalia, Tulare, Porterville, Finuba, '
            'Lindsay, Farmersville, Exeter, or Woodlake)')),
        (Counties.YOLO, _(
            'Yolo County (near Davis, West Sacramento, Winters, and '
            'Woodland)')),
        (Counties.VENTURA, _(
            'Ventura County (near Oxnard, Thousand Oaks, Simi Valley, '
            'Camarillo, Ojai, Moorpark, Fillmore, Santa Paula, or '
            'Ventura)')),
        (Counties.STANISLAUS, _(
            'Stanislaus County (near Modesto, Turlock, and Ceres)')),
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
    Counties.SANTA_CRUZ: CountyNames.SANTA_CRUZ,
    Counties.FRESNO: CountyNames.FRESNO,
    Counties.SONOMA: CountyNames.SONOMA,
    Counties.TULARE: CountyNames.TULARE,
    Counties.VENTURA: CountyNames.VENTURA,
    Counties.SANTA_BARBARA: CountyNames.SANTA_BARBARA,
    Counties.YOLO: CountyNames.YOLO,
    Counties.STANISLAUS: CountyNames.STANISLAUS,
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
