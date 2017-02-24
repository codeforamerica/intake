from django.db import models


class Address(models.Model):
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.CASCADE,
        related_name='addresses')
    name = models.TextField()
    text = models.TextField()
    walk_in_hours = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return self.text
