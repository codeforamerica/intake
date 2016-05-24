from django.db import models
from django.utils.crypto import get_random_string
from invitations.models import Invitation as BaseInvitation


class Organization(models.Model):
    name = models.CharField(max_length=50, unique=True)
    website = models.URLField(blank=True)
    blurb = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Invitation(BaseInvitation):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE
        )

    @classmethod
    def create(cls, email, organization, inviter=None):
        key = get_random_string(64).lower()
        return cls._default_manager.create(
            email=email,
            organization=organization,
            key=key,
            inviter=inviter
            )