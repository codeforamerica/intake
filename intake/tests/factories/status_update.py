import factory
from intake import models
from django.contrib.auth.models import User
from intake.tests.mock import fake
from .status_type import StatusTypeFactory


class StatusUpdateFactory(factory.DjangoModelFactory):
    status_type = factory.SubFactory(StatusTypeFactory)
    application = factory.Iterator(models.Application.objects.all())
    author = factory.Iterator(
        User.objects.filter(profile__organization__is_receiving_agency=True))
    additional_information = "just a little note"

    class Meta:
        model = models.StatusUpdate
