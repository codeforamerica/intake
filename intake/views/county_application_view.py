from django.shortcuts import redirect
from intake import utils
from django.core.urlresolvers import reverse, reverse_lazy
from .applicant_form_view_base import ApplicantFormViewBase
from formation.forms import county_form_selector
import intake.services.events_service as EventsService


class CountyApplicationNoWarningsView(ApplicantFormViewBase):
    """County application page that does *not* check for validation warnings.
    """
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')

    def get_form(self):
        Form = county_form_selector.get_combined_form_class(
            counties=self.county_slugs)
        if self.request.method in ('POST', 'PUT'):
            return Form(data=self.request.POST)
        elif self.request.method == 'GET':
            form_input_keys = set(Form.get_field_keys())
            session_data_keys = set(self.session_data.keys())
            session_and_form_overlap = \
                session_data_keys & form_input_keys
            if session_and_form_overlap:
                return Form(data=self.session_data, validate=True)
            else:
                # we have a new empty form with no existing session data
                return Form()

    def form_valid(self, form):
        # query org-based routing flags
        orgs = self.get_receiving_organizations(form)
        needs_declaration_letter = any([
            org.requires_declaration_letter for org in orgs])
        needs_rap_sheet = any([org.requires_rap_sheet for org in orgs])
        # route based on organization criteria
        if needs_declaration_letter:
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
            EventsService.log_form_page_complete(
                self.request, page_name=self.__class__.__name__)
            utils.save_form_data_to_session(
                self.request, self.session_key, form.data)
            return redirect(reverse('intake-confirm'))
        return super().form_valid(form)


county_application = CountyApplicationView.as_view()
confirm = CountyApplicationNoWarningsView.as_view()
