import logging
from urllib.parse import urljoin
from project.jinja2 import externalize_url
from django.db import models
from django.utils import timezone as timezone_utils
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

import intake

logger = logging.getLogger(__name__)


class ApplicationBundle(models.Model):
    submissions = models.ManyToManyField('intake.FormSubmission',
                                         related_name='bundles')
    organization = models.ForeignKey('user_accounts.Organization',
                                     models.PROTECT,
                                     related_name='bundles')
    bundled_pdf = models.FileField(upload_to='pdf_bundles/',
                                   null=True,
                                   blank=True)

    def should_have_a_pdf(self):
        """Returns `True` if `self.organization` has any `FillablePDF`
        """
        return bool(
            intake.models.FillablePDF.objects.filter(
                organization__bundles=self).count())

    def get_individual_filled_pdfs(self):
        """Gets FilledPDFs from this bundle's submissions and target_org
        """
        return intake.models.FilledPDF.objects.filter(
            submission__bundles=self,
            original_pdf__organization__bundles=self)

    def set_bundled_pdf_to_bytes(self, bytes_):
        """Sets the content of `self.pdf` to `bytes_`.
        """
        now_str = timezone_utils.now().strftime('%Y-%m-%d_%H:%M')
        filename = "submission_bundle_{0:0>4}-{1}.pdf".format(
            self.organization.pk, now_str)
        self.bundled_pdf = SimpleUploadedFile(
            filename, bytes_, content_type='application/pdf')

    def get_printout_url(self):
        return reverse(
            'intake-case_bundle_printout',
            kwargs=dict(bundle_id=self.id))

    def get_pdf_bundle_url(self):
        return reverse(
            'intake-app_bundle_detail_pdf',
            kwargs=dict(bundle_id=self.id))

    def get_absolute_url(self):
        return reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=self.id))

    def get_external_url(self):
        return externalize_url(self.get_absolute_url())
