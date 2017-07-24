from django.views.generic.base import View, TemplateView
from django.http import HttpResponse
from project.services import query_params
from intake.views.base_views import ViewAppDetailsMixin, AppIDQueryParamMixin
from intake.services import applications_service as AppsService
from intake.services import pdf_service as PDFService
from intake.services import messages_service as MessagesService


def get_multiple_apps_read_flash(count):
    amount = '{} applications' if count > 1 else '{} application'
    return str(
        amount + ' have been marked as “Read” and moved to the '
        '“Needs Status Update” folder.').format(count)


class PrebuiltPDFBundleWrapperView(
        ViewAppDetailsMixin, AppIDQueryParamMixin, TemplateView):
    """This view is an HTML page that includes an iframe for viewing the
    actual newapps pdf
    """
    template_name = "newapps_pdf_detail.jinja"

    def get_context_data(self):
        context = super().get_context_data()
        context['organization'] = self.organization
        context['app_count'] = AppsService.get_valid_application_ids_from_set(
            self.app_ids).count()
        # check for fillable pdfs
        needs_prebuilt = self.organization.pdfs.count() > 0
        if needs_prebuilt:
            context['pdf_url'] = query_params.get_url_for_ids(
                'intake-pdf_bundle_file_view', self.app_ids)
        else:
            context['pdf_url'] = query_params.get_url_for_ids(
                'intake-pdf_printout_for_apps', self.app_ids)
        AppsService.handle_apps_opened(self, self.app_ids)
        MessagesService.flash_success(
            self.request, get_multiple_apps_read_flash(context['app_count']))
        return context


class PrebuiltPDFBundleFileView(
        ViewAppDetailsMixin, AppIDQueryParamMixin, View):
    """This view returns the PDF file associated with a NewAppsPDF
        If the prebuilt pdf does not exist, it emails a warning and then builds
        one on the fly (which might time out)
    """
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        return response

    def request_valid(self, request):
        newapps_pdf = PDFService.get_or_create_prebuilt_pdf_for_app_ids(
            self.app_ids)
        return HttpResponse(
            newapps_pdf.pdf, content_type="application/pdf")


wrapper_view = PrebuiltPDFBundleWrapperView.as_view()
file_view = PrebuiltPDFBundleFileView.as_view()
