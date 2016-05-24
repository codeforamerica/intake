from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=50)
    website = models.URLField()
    blurb = models.TextField()

    def __str__(self):
        return self.name