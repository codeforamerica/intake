from django.db import models
from invitations.models import Invitation as BaseInvitation


class Organization(models.Model):
    name = models.CharField(max_length=50)
    website = models.URLField(blank=True)
    blurb = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Invitation(BaseInvitation):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE
        )