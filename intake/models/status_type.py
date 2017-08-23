from django.db import models
from .template_option import TemplateOption, TemplateOptionManager

# all of these are defined in the `template_options.json` fixture
CANT_PROCEED = 1
NO_CONVICTIONS = 2
NOT_ELIGIBLE = 3
ELIGIBLE = 4
COURT_DATE = 5
OUTCOME_GRANTED = 6
OUTCOME_DENIED = 7
TRANSFERRED = 8


class PurgedStatusType(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_statustype'
        managed = False


class StatusType(TemplateOption):
    objects = TemplateOptionManager()
