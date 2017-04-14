from intake import utils
from django.views.generic.base import TemplateView
from .applicant_form_view_base import ApplicantFormViewBase


class ThanksView(TemplateView):

    def get_context_data(self):
        context = super().get_context_data()
        utils.clear_session_data(
            self.request, ApplicantFormViewBase.session_key)
        return context


class RAPSheetInstructions(TemplateView):

    def get_context_data(self):
        utils.clear_session_data(
            self.request, ApplicantFormViewBase.session_key)
        pass
