from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from intake import models
import intake.services.pdf_service as PDFService
import intake.services.applications_service as AppsService
from intake.views.base_views import (
    ViewAppDetailsMixin, AppIDQueryParamMixin, not_allowed)
from intake.views.app_detail_views import ApplicationDetail


class CasePrintoutPDFView(ApplicationDetail):
    """Serves a PDF with full case details, based on the details
    needed by the user's organization

    The PDF is created on the fly
    """
    def get(self, request, submission_id):
        submission = get_object_or_404(
            models.FormSubmission, pk=int(submission_id))
        if not submission.organizations.filter(
                id=request.user.profile.organization_id).exists():
            return not_allowed(request)
        apps = AppsService.filter_to_org_if_not_staff(
            submission.applications.all(), request.user)
        AppsService.handle_apps_opened(
            self, apps, send_slack_notification=False)
        filename, pdf_bytes = PDFService.get_printout_for_submission(
            request.user, submission)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response


class PrintoutForApplicationsView(
        ViewAppDetailsMixin, AppIDQueryParamMixin, View):
    def request_valid(self, request, *args, **kwargs):
        apps = models.Application.objects.filter(id__in=self.app_ids)
        filename, pdf_bytes = \
            PDFService.get_concatenated_printout_for_applications(apps)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response

printout_for_apps = PrintoutForApplicationsView.as_view()
printout_for_submission = CasePrintoutPDFView.as_view()
