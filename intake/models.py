import importlib
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from pytz import timezone

from . import pdfparser, anonymous_names


nice_contact_choices = {
    'voicemail': 'voicemail',
    'sms': 'text message',
    'email': 'email',
    'snailmail': 'paper mail'
}


def get_parser():
    parser = pdfparser.PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
        'intake/pdfparser.jar')
    return parser


class FormSubmission(models.Model):
    '''This is 
    '''
    answers = JSONField()
    # old_uuid is only used for porting legacy applications
    old_uuid = models.CharField(max_length=34, blank=True)
    anonymous_name = models.CharField(max_length=60,
        default=anonymous_names.generate)
    date_received = models.DateTimeField(auto_now_add=True)
    reviewed_by_staff = models.DateTimeField(null=True)
    confirmation_sent = models.DateTimeField(null=True)
    submitted_to_agency = models.DateTimeField(null=True)
    opened_by_agency = models.DateTimeField(null=True)
    processed_by_agency = models.DateTimeField(null=True)
    due_for_followup = models.DateTimeField(null=True)
    followup_sent = models.DateTimeField(null=True)
    followup_answered = models.DateTimeField(null=True)
    told_eligible = models.DateTimeField(null=True)
    told_ineligible = models.DateTimeField(null=True)

    def get_local_date_received(self, fmt, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        return self.date_received.astimezone(local_tz).strftime(fmt)

    def get_contact_preferences(self):
        preferences = []
        for k in self.answers:
            if "prefers" in k:
                preferences.append(k[8:])
        return [nice_contact_choices[m] for m in preferences]

    def get_anonymous_display(self):
        return self.anonymous_name

    def __str__(self):
        return self.get_anonymous_display()



class ApplicationLogEntry(models.Model):
    '''
    '''
    CREATED = 1
    READ = 2
    UPDATED = 3
    DELETED = 4

    ACTION_TYPES = (
        (CREATED, "created"),
        (READ,    "read"   ),
        (UPDATED, "updated"),
        (DELETED, "deleted"), 
        )

    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,
        on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(FormSubmission,
        on_delete=models.SET_NULL, null=True)
    action_type = models.PositiveSmallIntegerField(
        choices=ACTION_TYPES)
    updated_field = models.CharField(max_length=50,
        blank=True)



class FillablePDF(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='pdfs/')
    translator = models.TextField()

    def get_pdf(self):
        self.pdf.seek(0)
        return self.pdf

    def get_translator(self):
        import_path_parts = self.translator.split('.')
        callable_name = import_path_parts.pop()
        module_path = '.'.join(import_path_parts)
        module = importlib.import_module(module_path)
        return getattr(module, callable_name)

    def get_pdf_fields(self):
        parser = get_parser()
        data = parser.get_field_data(self.get_pdf())
        return data['fields']

    def fill(self, *args, **kwargs):
        parser = get_parser()
        translator = self.get_translator()
        return parser.fill_pdf(self.get_pdf(), translator(*args, **kwargs))

    def fill_many(self, data_set, *args, **kwargs):
        parser = get_parser()
        translator = self.get_translator()
        return parser.fill_many_pdfs(self.get_pdf(), [
            translator(d, *args, **kwargs)
            for d in data_set
            ])
