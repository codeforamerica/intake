from django.db import models
from intake.constants import PACIFIC_TIME
from intake.models.abstract_base_models import BaseModel


class PrebuiltMultiAppPDF(BaseModel):
    # includes created, updated from BaseModel
    applications = models.ManyToManyField(
        'intake.Application',
        related_name='prebuilt_multiapp_pdfs')
    pdf = models.FileField(upload_to='prebuilt_multiapp_pdfs/')
    organization = models.ForeignKey(
        'user_accounts.Organization',
        related_name='prebuilt_multiapp_pdfs',
        on_delete=models.PROTECT)

    def __str__(self):
        return str(
            'PDF for {apps_count} applications to {org_name}. '
            'Last built: {updated}').format(
                apps_count=self.applications.count(),
                org_name=self.organization.name,
                updated=self.updated.astimezone(
                    PACIFIC_TIME).strftime('%Y-%m-%d %H:%M'))
