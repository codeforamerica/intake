from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from pytz import timezone

PACIFIC_TIME = timezone('US/Pacific')
LANGUAGES_LOOKUP = dict(settings.LANGUAGES)

# Communication methods
SMS = 'sms'
EMAIL = 'email'
VOICEMAIL = 'voicemail'
SNAILMAIL = 'snailmail'

COUNTY_NOT_LISTED_HANDLED_TAG = 'cnl_done'

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

APPROVE_APPLICATION = 'approve_application'
EDIT_APPLICATION = 'edit_application'

DECLARATION_LETTER_REVIEW_CHOICES = (
    (EDIT_LETTER, _('Edit letter')),
    (APPROVE_LETTER, _('Approve letter')),
)

APPLICATION_REVIEW_CHOICES = (
    (APPROVE_APPLICATION, _('Approve application')),
)

STAFF_NAME_CHOICES = ['Jazmyn', 'Ben']


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
