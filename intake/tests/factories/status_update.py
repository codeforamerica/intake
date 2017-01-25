import factory
from intake import models
from django.contrib.auth.models import User
from .status_type import StatusTypeFactory


class StatusUpdateFactory(factory.DjangoModelFactory):

    status_type = factory.Iterator(models.StatusType.objects.all())
    application = factory.Iterator(models.Application.objects.all())
    author = factory.Iterator(
        User.objects.filter(profile__organization__is_receiving_agency=True))
    additional_information = "just a little note"

    class Meta:
        model = models.StatusUpdate

    @classmethod
    def create(cls, *args, **kwargs):
        next_steps = kwargs.pop('next_steps', [])
        instance = super().create(*args, **kwargs)
        if not next_steps:
            step = models.NextStep.objects.first()
            next_steps = [step]
        instance.next_steps.add(*next_steps)
        instance.save()
        return instance
