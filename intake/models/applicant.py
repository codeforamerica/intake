from django.db import models
import intake


class Permissions:
    CAN_SEE_APP_STATS = 'Can see detailed aggregate information about apps'
    CAN_SEE_APP_DETAILS = 'Can see detail information about individual apps'


class Applicant(models.Model):
    visitor = models.ForeignKey('intake.Visitor', null=True)

    # permissions

    class Meta:
        permissions = (
            ('view_app_stats', Permissions.CAN_SEE_APP_STATS),
            ('view_app_details', Permissions.CAN_SEE_APP_DETAILS),
        )

    def log_event(self, name, data=None):
        data = data or {}
        return intake.models.ApplicationEvent.create(
            name=name,
            applicant_id=self.id,
            **data
        )
