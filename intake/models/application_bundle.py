
import logging
from urllib.parse import urljoin

from django.db import models
from django.utils import timezone as timezone_utils
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.conf import settings

import intake

logger = logging.getLogger(__name__)


class ApplicationBundle(models.Model):
    submissions = models.ManyToManyField('intake.FormSubmission',
                                         related_name='bundles')
    organization = models.ForeignKey('user_accounts.Organization',
                                     on_delete=models.PROTECT,
                                     related_name='bundles')
    bundled_pdf = models.FileField(upload_to='pdf_bundles/', null=True,
                                   blank=True)

    @classmethod
    def create_with_submissions(cls, submissions, skip_pdf=False, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        if submissions:
            instance.submissions.add(*submissions)
        if not skip_pdf and not instance.bundled_pdf:
            instance.build_bundled_pdf_if_necessary()
        return instance

    @classmethod
    def get_or_create_for_submissions_and_user(cls, submissions, user):
        query = cls.objects.all()
        for sub in submissions:
            query = query.filter(submissions=sub)
        if not user.is_staff:
            query = query.filter(organization=user.profile.organization)
        query = query.first()
        if not query:
            query = cls.create_with_submissions(
                submissions,
                organization=user.profile.organization)
        return query

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

    def build_bundled_pdf_if_necessary(self):
        """Populates `self.bundled_pdf` attribute if needed

        First checks whether or not there should be a pdf. If so,
        - tries to grab filled pdfs for this bundles submissionts
        - if it needs a pdf but there weren't any pdfs, it logs an error and
          creates the necessary filled pdfs.
        - makes a filename based on the organization and current time.
        - adds the file data and saves itself.
        """
        needs_pdf = self.should_have_a_pdf()
        if not needs_pdf:
            return
        submissions = self.submissions.all()
        filled_pdfs = self.get_individual_filled_pdfs()
        missing_filled_pdfs = (
            not filled_pdfs or (len(submissions) > len(filled_pdfs)))
        if needs_pdf and missing_filled_pdfs:
            msg = str(
                "Submissions for ApplicationBundle(pk={}) lack pdfs"
                ).format(self.pk)
            logger.error(msg)
            intake.notifications.slack_simple.send(msg)
            for submission in submissions:
                submission.fill_pdfs()
            filled_pdfs = self.get_individual_filled_pdfs()
        if len(filled_pdfs) == 1:
            self.set_bundled_pdf_to_bytes(filled_pdfs[0].pdf.read())
        else:
            self.set_bundled_pdf_to_bytes(
                intake.models.get_parser().join_pdfs(
                    filled.pdf for filled in filled_pdfs))
        self.save()

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
        return urljoin(settings.DEFAULT_HOST, self.get_absolute_url())
