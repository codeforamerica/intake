from django.db import models
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from project.services import query_params
from intake.constants import PACIFIC_TIME
from intake.models.abstract_base_models import BaseModel


class PrebuiltPDFBundle(BaseModel):
    # includes created, updated from BaseModel
    applications = models.ManyToManyField(
        'intake.Application',
        related_name='prebuilt_multiapp_pdfs')
    pdf = models.FileField(upload_to='prebuilt_newapps_pdfs/')
    organization = models.ForeignKey(
        'user_accounts.Organization',
        models.PROTECT,
        related_name='prebuilt_pdf_bundles',
        )

    def set_bytes(self, bytes_):
        if not bytes_:
            self.pdf = None
        else:
            now_str = timezone.now().astimezone(
                PACIFIC_TIME).strftime('%Y-%m-%d_%H:%M')
            filename = '{}_newapps_{}.pdf'.format(
                self.organization.slug, now_str)
            self.pdf = SimpleUploadedFile(
                filename, bytes_, content_type='application/pdf')

    def get_absolute_url(self):
        return query_params.get_url_for_ids(
            'intake-pdf_bundle_file_view',
            self.applications.values_list('id', flat=True))

    def __str__(self):
        status = 'Prebuilt' if self.pdf else 'Unbuilt'
        return str(
            '{status} PDF Bundle for {apps_count} applications to {org_name}. '
            'Updated: {updated}').format(
                status=status,
                apps_count=self.applications.count(),
                org_name=self.organization.name,
                updated=self.updated.astimezone(
                    PACIFIC_TIME).strftime('%Y-%m-%d %H:%M %Z'))
