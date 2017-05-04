import uuid
from django.db import models


class Visitor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    first_visit = models.DateTimeField(auto_now_add=True)
    source = models.TextField(null=True)
    referrer = models.TextField(null=True)
    ip_address = models.TextField(null=True)

    def get_uuid(self):
        return self.uuid.hex
