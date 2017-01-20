from django.db import models
from django.contrib.postgres.fields import JSONField


class StatusNotification(models.Model):
    status_update = models.ForeignKey(
        'intake.StatusUpdate', on_delete=models.PROTECT)
    contact_info = JSONField()
    base_message = models.TextField()
    sent_message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
