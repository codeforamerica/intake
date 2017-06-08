from django.db import models
from intake.models.abstract_base_models import BaseModel
from intake.constants import PACIFIC_TIME


class PartnershipLead(BaseModel):
    # includes created, & updated fields from BaseModel
    visitor = models.ForeignKey(
        'intake.Visitor', on_delete=models.PROTECT,
        related_name='partnership_leads')
    name = models.TextField()
    email = models.EmailField()
    organization_name = models.TextField()
    message = models.TextField(blank=True)

    def __str__(self):
        datetime = self.created.astimezone(
            PACIFIC_TIME).strftime('%Y-%m-%d %H:%M %Z')
        return '{} {} <{}> from {}'.format(
            datetime, self.name, self.email, self.organization_name)
