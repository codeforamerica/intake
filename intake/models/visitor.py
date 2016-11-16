from django.db import models


class Visitor(models.Model):
    first_visit = models.DateTimeField(auto_now_add=True)
    source = models.TextField(null=True)
    referrer = models.TextField(null=True)
