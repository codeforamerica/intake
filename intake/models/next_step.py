from django.db import models
from .template_option import TemplateOption, TemplateOptionManager


class PurgedNextStep(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_nextstep'
        managed = False


class NextStep(TemplateOption):
    objects = TemplateOptionManager()
