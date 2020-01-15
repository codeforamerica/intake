import importlib

from django.db import models

from intake import pdfparser
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


def get_parser():
    parser = pdfparser.PDFParser()
    parser.PDFPARSER_PATH = getattr(settings, 'PDFPARSER_PATH',
                                    'intake/pdfparser.jar')
    return parser


class FillablePDF(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='pdfs/')
    translator = models.TextField()
    organization = models.ForeignKey(
        'user_accounts.Organization',
        models.CASCADE,
        related_name='pdfs',
        null=True
    )

    @classmethod
    def get_default_instance(cls):
        return cls.objects.first()

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

    def __str__(self):
        return self.name

    def fill_for_submission(self, submission):
        """Fills out a pdf and saves it as a FilledPDF instance

        used when saving a new submission
        used when retrieving a filled pdf if it doesn't
        """
        return FilledPDF.create_with_pdf_bytes(
            pdf_bytes=self.fill(submission),
            original_pdf=self,
            submission=submission
        )

    def fill(self, *args, **kwargs):
        parser = get_parser()
        translator = self.get_translator()
        return parser.fill_pdf(self.get_pdf(), translator(*args, **kwargs))

    def fill_many(self, data_set, *args, **kwargs):
        if data_set:
            parser = get_parser()
            translator = self.get_translator()
            translated = [translator(d, *args, **kwargs)
                          for d in data_set]
            if len(translated) == 1:
                return parser.fill_pdf(self.get_pdf(), translated[0])
            return parser.fill_many_pdfs(self.get_pdf(), translated)


class FilledPDF(models.Model):
    """A FillablePDF filled with FormSubmission data.
    """
    pdf = models.FileField(upload_to='filled_pdfs/')
    original_pdf = models.ForeignKey(
        FillablePDF,
        on_delete=models.SET_NULL,
        related_name='filled_copies',
        null=True)
    submission = models.ForeignKey(
        'intake.FormSubmission',
        on_delete=models.CASCADE,
        related_name='filled_pdfs')

    @classmethod
    def create_with_pdf_bytes(cls, pdf_bytes, original_pdf, submission):
        """Sets the contents of `self.pdf` to `bytes_`.
        """
        filename = 'filled_{0:0>4}-{1:0>6}.pdf'.format(
            original_pdf.id, submission.id)
        file_obj = SimpleUploadedFile(
            filename, pdf_bytes, content_type='application/pdf')
        instance = cls(
            pdf=file_obj,
            original_pdf=original_pdf,
            submission=submission)
        instance.save()
        return instance

    def get_absolute_url(self):
        """This is unique _to each submission_.

        URLs will need to be changed when multiple pdfs can pertain to one
        submission
        """
        return reverse(
            'intake-filled_pdf',
            kwargs=dict(submission_id=self.submission.id))
