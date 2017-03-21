from django.db import models
from .abstract_base_models import BaseModel


class ApplicationTransfer(BaseModel):
    """A record that links a 'Transferred' status update to the new application
    created from the transfer.
    """
    status_update = models.OneToOneField(
        'intake.StatusUpdate', related_name='transfer',
        on_delete=models.CASCADE)
    new_application = models.ForeignKey(
        'intake.Application', related_name='incoming_transfers',
        on_delete=models.PROTECT)
    reason = models.TextField(blank=True)

    def __str__(self):
        return '{} because "{}"'.format(
            self.status_update.__str__(),
            self.reason)
