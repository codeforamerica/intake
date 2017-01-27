from django.db import models
from django.contrib.postgres.fields import JSONField


class StatusNotification(models.Model):
    status_update = models.OneToOneField(
        'intake.StatusUpdate', on_delete=models.PROTECT,
        related_name="notification")
    contact_info = JSONField()
    base_message = models.TextField()
    sent_message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status_update.status_type.display_name
