from .base_factory import PrepopulatedModelFactory
from user_accounts import models

OrganizationFactory = PrepopulatedModelFactory(
    models.Organization.objects.filter(is_receiving_agency=True))

TransferOrganizationFactory = PrepopulatedModelFactory(
    models.Organization.objects.filter(can_transfer_applications=True))
