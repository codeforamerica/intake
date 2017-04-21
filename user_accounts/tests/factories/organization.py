from .base_factory import PrepopulatedModelFactory
from user_accounts import models


class OrganizationFactory(PrepopulatedModelFactory):
    @classmethod
    def get_queryset(cls):
        return models.Organization.objects.filter(is_receiving_agency=True)


class TransferOrganizationFactory(PrepopulatedModelFactory):
    @classmethod
    def get_queryset(cls):
        return models.Organization.objects.filter(
            can_transfer_applications=True)
