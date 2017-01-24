from django.db import models
import intake
from intake.permissions import (
    CAN_SEE_APP_STATS,
    CAN_SEE_APP_DETAILS
    )


class Applicant(models.Model):
    visitor = models.ForeignKey('intake.Visitor', null=True)

    class Meta:
        permissions = (
            ('view_app_stats',
                'Can see detailed aggregate information about apps'),
            ('view_app_details',
                'Can see detail information about individual apps'),
        )

    def log_event(self, name, data=None):
        data = data or {}
        return intake.models.ApplicationEvent.create(
            name=name,
            applicant_id=self.id,
            **data
        )
