from django.db import models
import uuid


class Visitor(models.Model):
    first_visit = models.DateTimeField(auto_now_add=True)
    source = models.TextField(null=True)
    referrer = models.TextField(null=True)
    ip_address = models.TextField(null=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
