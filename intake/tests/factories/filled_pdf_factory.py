import os
from django.core.files.uploadedfile import SimpleUploadedFile
import factory
from django.conf import settings
from intake import models
from user_accounts.models import Organization
from .fillable_pdf_factory import FillablePDFFactory
from .form_submission_factory import FormSubmissionWithOrgsFactory


FILLED_SAMPLE_FORM_PATH = os.path.join(
    settings.REPO_DIR, 'tests/sample_pdfs/sample_form_filled.pdf')


def make_sub_to_sf(*args, **kwargs):
    return FormSubmissionWithOrgsFactory(
        organizations=Organization.objects.filter(slug='sf_pubdef'))


def set_to_sample_form(*args, **kwargs):
    data = open(FILLED_SAMPLE_FORM_PATH, 'rb').read()
    return SimpleUploadedFile(
        content=data, name="sample_form_filled.pdf",
        content_type="application/pdf")


class FilledPDFFactory(factory.DjangoModelFactory):
    pdf = factory.LazyFunction(set_to_sample_form)
    original_pdf = factory.SubFactory(FillablePDFFactory)
    submission = factory.LazyFunction(make_sub_to_sf)

    class Meta:
        model = models.FilledPDF
