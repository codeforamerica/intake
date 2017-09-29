from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, reverse_lazy

from project import alerts
from .applicant_form_view_base import ApplicantFormViewBase
from formation.forms import county_form_selector, \
    county_display_form_selector, ApplicationReviewForm
import intake.services.messages_service as MessagesService
from intake.constants import EDIT_APPLICATION
from intake.serializers import RequestSerializer
from project.services import logging_service

WARNING_FLASH_MESSAGE = _(
    "Please double check the form. Some parts are empty and may cause delays.")


class CountyApplicationNoWarningsView(ApplicantFormViewBase):
    """County application page that does *not* check for validation warnings.
    """
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-review')

    def get_form_class(self):
        return county_form_selector.get_combined_form_class(
            counties=self.county_slugs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        editing_scope = self.request.GET.get('editing', '')
        if editing_scope:
            MessagesService.flash_warnings(
                self.request,
                _("You wanted to edit your application"))
        field_to_edit = context['form'].fields.get(editing_scope, None)
        if field_to_edit:
            field_to_edit.add_warning(
                _("You wanted to edit your answer to this question."),
                key=editing_scope)
        return context


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


class CountyApplicationReviewView(ApplicantFormViewBase):
    """County application review page"""
    template_name = "forms/county_form_review.jinja"
    success_url = reverse_lazy('intake-thanks')

    def get_form_class(self):
        # The default form is a DisplayForm based on the appropriate combinable
        # county form spec.
        form_class = county_display_form_selector.get_combined_form_class(
            counties=self.county_slugs)
        return form_class

    def get_form(self, form_class=None):
        # If it's a POST we'll swap in this ApplicationReviewForm that just
        # has a choice field for whether the user wants to go back and edit
        # their application or continue. Otherwise we'll use the county display
        # form as specified in get_form_class
        if self.request.method in ('POST', 'PUT'):
            return ApplicationReviewForm(data=self.request.POST)
        county_form = super().get_form(form_class)
        county_form.display_template_name = "forms/county_form_display.jinja"
        return county_form

    def get_county_form(self):
        """
        Create a county form with all the data from the session.

        :return: a county form
        """
        form_class = self.get_form_class()
        form_kwargs = super().get_form_kwargs()
        if self.has_form_data_in_session():
            form_kwargs.update(data=self.session_data, validate=True)
        return form_class(**form_kwargs)

    def get_context_data(self, *args, **kwargs):
        # If any of the receiving organizations will need a letter of
        # declaration, we'll want to display some different copy in the form,
        # so add it to the context.
        context_data = super().get_context_data(*args, **kwargs)
        orgs = self.get_receiving_organizations(self.get_county_form())
        needs_declaration_letter = any([
            org.requires_declaration_letter for org in orgs])
        context_data.update(needs_declaration_letter=needs_declaration_letter)
        return context_data

    def post(self, request, *args, **kwargs):
        """
        Overriding post so we can check the special ApplicationReviewForm just
        to determine the next step, and and then re-create the combined county
        form for validation if we are continuing.
        """
        # Fist validate the ApplicationReviewForm and check if the user chose
        # to go back and edit their application or continue.
        review_form = self.get_form()
        if review_form.is_valid():
            answer = review_form.cleaned_data['submit_action']
            if answer == EDIT_APPLICATION:
                # The user has chosen to go back and edit, redirect them
                return redirect(reverse('intake-county_application'))

            # Re-create the original county form with all the application data
            # from the session, and validate as usual
            county_form = self.get_county_form()
            if county_form.is_valid():
                return self.form_valid(county_form)
            else:
                subject = 'Invalid form data at review page'
                serialized_request = RequestSerializer(request).data
                message = 'Check the logs:\n{}'.format(serialized_request)
                alerts.send_email_to_admins(subject=subject, message=message)
                logging_service.format_and_log(
                    'application_error', level='error', **serialized_request)
                return redirect('intake-county_application')
        else:
            return self.form_invalid(review_form)

    def form_valid(self, form):
        # Check if any of the receiving organizations require a letter of
        # declaration and redirect before saving if so.
        orgs = self.get_receiving_organizations(form)
        needs_declaration_letter = any([
            org.requires_declaration_letter for org in orgs])
        if needs_declaration_letter:
            self.log_page_completion_and_save_data(form)
            return redirect('intake-write_letter')

        # No declaration needed, save the application
        self.finalize_application(form)

        # Redirect after saving if a rap sheet is needed.
        needs_rap_sheet = any([org.requires_rap_sheet for org in orgs])
        if needs_rap_sheet:
            self.success_url = reverse('intake-rap_sheet')
        return super().form_valid(form)


county_application = CountyApplicationView.as_view()
confirm = CountyApplicationNoWarningsView.as_view()
review = CountyApplicationReviewView.as_view()
