from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, reverse_lazy
from .applicant_form_view_base import ApplicantFormViewBase
from formation.forms import county_form_selector
import intake.services.messages_service as MessagesService


WARNING_FLASH_MESSAGE = _(
    "Please double check the form. Some parts are empty and may cause delays.")


class CountyApplicationNoWarningsView(ApplicantFormViewBase):
    """County application page that does *not* check for validation warnings.
    """
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')

    def get_form_class(self):
        return county_form_selector.get_combined_form_class(
            counties=self.county_slugs)

    def form_valid(self, form):
        # query org-based routing flags
        orgs = self.get_receiving_organizations(form)
        needs_declaration_letter = any([
            org.requires_declaration_letter for org in orgs])
        needs_rap_sheet = any([org.requires_rap_sheet for org in orgs])
        # route based on organization criteria
        if needs_declaration_letter:
            self.log_page_completion_and_save_data(form)
            return redirect('intake-write_letter')
        self.finalize_application(form)
        if needs_rap_sheet:
            self.success_url = reverse('intake-rap_sheet')
        return super().form_valid(form)


class CountyApplicationView(CountyApplicationNoWarningsView):
    """County application page that checks for validation warnings.
    """

    def form_valid(self, form):
        """If no errors, check for warnings, redirect to confirmation if needed
        """
        if form.warnings:
            self.log_page_completion_and_save_data(form)
            MessagesService.flash_warnings(self.request, WARNING_FLASH_MESSAGE)
            return redirect(reverse('intake-confirm'))
        return super().form_valid(form)


county_application = CountyApplicationView.as_view()
confirm = CountyApplicationNoWarningsView.as_view()
