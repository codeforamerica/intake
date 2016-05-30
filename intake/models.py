import importlib
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.postgres.fields import JSONField
from pytz import timezone

from .pdfparser import PDFParser

nice_contact_choices = {
    'voicemail': 'Voicemail',
    'sms': 'Text Message',
    'email': 'Email',
    'snailmail': 'Paper mail'
}


def get_parser():
    parser = PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
        'intake/pdfparser.jar')
    return parser


class FormSubmission(models.Model):
    date_received = models.DateTimeField(auto_now_add=True)
    answers = JSONField()

    def get_local_date_received(self, fmt, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        return self.date_received.astimezone(local_tz).strftime(fmt)

    def get_contact_preferences(self):
        preferences = []
        for k in self.answers:
            if "prefers" in k:
                preferences.append(k[8:])
        return [nice_contact_choices[m] for m in preferences]


class FillablePDF(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='pdfs/')
    translator = models.TextField()

    def get_pdf(self):
        self.pdf.seek(0)
        return self.pdf

    def fill(self, *args, **kwargs):
        parser = get_parser()
        import_path_parts = self.translator.split('.')
        callable_name = import_path_parts.pop()
        module_path = '.'.join(import_path_parts)
        module = importlib.import_module(module_path)
        translator = getattr(module, callable_name)
        return parser.fill_pdf(self.get_pdf(), translator(*args, **kwargs))

    def get_pdf_fields(self):
        parser = get_parser()
        data = parser.get_field_data(self.get_pdf())
        return data['fields']
