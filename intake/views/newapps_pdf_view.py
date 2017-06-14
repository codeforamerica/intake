from django.views.generic.base import View, TemplateView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from intake.views.base_views import ViewAppDetailsMixin
from intake.views.app_detail_views import not_allowed
from intake.services import applications_service as AppsService
from intake.services import pdf_service as PDFService
from intake import models


class NewAppsPDFDetailMixin:
    """This is a mixin for checking permissions to read a newapps pdf
    """
    def check_permission(self, request, newapps_pdf_id):
        self.newapps_pdf = get_object_or_404(
            models.NewAppsPDF, pk=int(newapps_pdf_id))
        self.profile = request.user.profile
        self.organization = self.profile.organization
        has_access = (self.organization == self.newapps_pdf.organization)
        if not has_access:
            return not_allowed(request)


class NewAppsPDFWrapperView(
        ViewAppDetailsMixin, NewAppsPDFDetailMixin, TemplateView):
    """This view is an HTML page that includes an iframe for viewing the
    actual newapps pdf
    """
    template_name = "newapps_pdf_detail.jinja"

    def get(self, *args, **kwargs):
        redirect = self.check_permission(*args, **kwargs)
        if redirect:
            return redirect
        else:
            return super().get(*args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        unread_count = AppsService.get_unread_applications_for_org(
            self.organization).count()
        newapps_pdf_count = self.newapps_pdf.applications.count()
        if unread_count != newapps_pdf_count:
            # build on the fly? What if this takes forever?
            self.newapps_pdf = \
                PDFService.prebuild_newapps_pdf_for_san_francisco()
            newapps_pdf_count = self.newapps_pdf.applications.count()
        context['app_count'] = newapps_pdf_count
        has_apps = context['app_count'] > 0 and self.newapps_pdf.pdf
        context['newapps_pdf_is_empty'] = not has_apps
        context['newapps_pdf'] = self.newapps_pdf
        context['organization'] = self.organization
        return context


class NewAppsPDFFileView(ViewAppDetailsMixin, NewAppsPDFDetailMixin, View):
    """This view returns the PDF file associated with a NewAppsPDF
    """
    def get(self, *args, **kwargs):
        redirect = self.check_permission(*args, **kwargs)
        if redirect:
            return redirect
        else:
            return HttpResponse(
                self.newapps_pdf.pdf, content_type="application/pdf")
