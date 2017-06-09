from django.db import models
from intake.constants import PACIFIC_TIME
from intake.models.abstract_base_models import BaseModel


class NewAppsPDF(BaseModel):
    # includes created, updated from BaseModel
    applications = models.ManyToManyField(
        'intake.Application',
        related_name='prebuilt_multiapp_pdfs')
    pdf = models.FileField(upload_to='prebuilt_multiapp_pdfs/')
    organization = models.OneToOneField(
        'user_accounts.Organization', related_name='newapps_pdf',
        on_delete=models.PROTECT)

    def set_bytes(self, bytes_):
        pass

    def get_bytes(self, bytes_):
        pass

    def __str__(self):
        status = 'Prebuilt' if self.pdf else 'Unbuilt'
        return str(
            '{status} NewAppsPDF for {apps_count} applications to {org_name}. '
            'Updated: {updated}').format(
                status=status,
                apps_count=self.applications.count(),
                org_name=self.organization.name,
                updated=self.updated.astimezone(
                    PACIFIC_TIME).strftime('%Y-%m-%d %H:%M %Z'))
