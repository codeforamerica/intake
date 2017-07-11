import factory
from .base_factory import PrepopulatedModelFactory
from user_accounts import models


class ExistingOrganizationFactory(PrepopulatedModelFactory):
    @classmethod
    def get_queryset(cls):
        return models.Organization.objects.filter(is_receiving_agency=True)


class TransferOrganizationFactory(PrepopulatedModelFactory):
    @classmethod
    def get_queryset(cls):
        return models.Organization.objects.filter(
            can_transfer_applications=True)


class FakeOrganizationFactory(factory.DjangoModelFactory):
    slug = factory.Sequence(lambda n: 'org-{}'.format(n))
    name = factory.Sequence(lambda n: 'Fake Org {}'.format(n))
    is_checking_notifications = True
    is_receiving_agency = True

    class Meta:
        model = models.Organization
