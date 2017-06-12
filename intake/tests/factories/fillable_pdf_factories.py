import factory
from intake import models
from user_accounts.models import Organization


def get_sf_pubdef(*args, **kwargs):
    return Organization.objects.get(slug="sf_pubdef")


class FillablePDFFactory(factory.DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Fake FillablePDF {}'.format(n))
    pdf = factory.django.FileField(
        filename='tests/sample_pdfs/sample_form.pdf')
    translator = 'tests.sample_translator.translate'
    organization = factory.LazyFunction(get_sf_pubdef)

    class Meta:
        model = models.FillablePDF
