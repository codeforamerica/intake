import factory
from django.core.files import File
from intake import models
from user_accounts.models import Organization


def get_sf_pubdef(*args, **kwargs):
    return Organization.objects.get(slug="sf_pubdef")


def get_sample_pdf(*args, **kwargs):
    return File(open('tests/sample_pdfs/sample_form.pdf', 'rb'))


class FillablePDFFactory(factory.DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Fake FillablePDF {}'.format(n))
    pdf = factory.LazyFunction(get_sample_pdf),
    translator = "tests.sample_translator.translate",
    organization = factory.LazyFunction(get_sf_pubdef)

    class Meta:
        model = models.FillablePDF
