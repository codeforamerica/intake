import factory
from intake import models
from django.contrib.auth.models import User
from .status_notification_factory import StatusNotificationFactory


class StatusUpdateFactory(factory.DjangoModelFactory):

    status_type = factory.Iterator(models.StatusType.objects.filter(
        is_a_status_update_choice=True))
    application = factory.Iterator(models.Application.objects.all())
    author = factory.Iterator(
        User.objects.filter(profile__organization__is_receiving_agency=True))
    additional_information = "We may be able to get a fee waived for you"
    other_next_step = "Come to our Walk-In Clinic"

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


class StatusUpdateWithNotificationFactory(StatusUpdateFactory):
    notification = factory.RelatedFactory(
        StatusNotificationFactory, 'status_update')
