from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=50)
    website = models.URLField(blank=True)
    blurb = models.TextField(blank=True)

    def __str__(self):
        return self.name