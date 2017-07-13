import os
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import factory
from intake import models
from user_accounts.models import Organization


SAMPLE_FORM_PATH = os.path.join(
    settings.REPO_DIR, 'tests/sample_pdfs/sample_form.pdf')


def get_sf_pubdef(*args, **kwargs):
    return Organization.objects.get(slug="sf_pubdef")


def set_to_sample_form(*args, **kwargs):
    data = open(SAMPLE_FORM_PATH, 'rb').read()
    return SimpleUploadedFile(
        content=data, name="sample_form.pdf", content_type="application/pdf")


class FillablePDFFactory(factory.DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Fake FillablePDF {}'.format(n))
    pdf = factory.LazyFunction(set_to_sample_form)
    translator = 'tests.sample_translator.translate'
    organization = factory.LazyFunction(get_sf_pubdef)

    class Meta:
        model = models.FillablePDF
