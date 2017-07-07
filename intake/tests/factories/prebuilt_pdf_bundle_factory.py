import factory
from intake import models
from user_accounts.models import Organization


def get_sf_pubdef(*args, **kwargs):
    return Organization.objects.get(slug="sf_pubdef")


class PrebuiltPDFBundleFactory(factory.DjangoModelFactory):
    organization = factory.LazyFunction(get_sf_pubdef)

    class Meta:
        model = models.PrebuiltPDFBundle
