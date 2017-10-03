from django.db import models
from .template_option import TemplateOption, TemplateOptionManager


class PurgedStatusType(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_statustype'
        managed = False


class StatusType(TemplateOption):
    objects = TemplateOptionManager()
