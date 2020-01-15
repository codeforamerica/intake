from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from intake import models, utils
import intake.services.events_service as EventsService
import intake.services.messages_service as MessagesService
import logging
from django.shortcuts import redirect
from django.urls import reverse
from intake.exceptions import (
    NoCountiesInSessionError, NoApplicantInSessionError)
import intake.services.submissions as SubmissionsService
import intake.services.applicants as ApplicantsService
from project.jinja2 import oxford_comma


ERROR_MESSAGE = _(
    "There were some problems with your application. "
    "Please check the errors below.")

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ApplicantFormViewBase(FormView):
    session_key = 'form_in_progress'

    def has_form_data_in_session(self):
        form_keys = set(self.get_form_class().get_field_keys())
        session_data_keys = set(self.session_data.keys())
        return bool(form_keys & session_data_keys)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            if self.has_form_data_in_session():
                form_kwargs.update(data=self.session_data, validate=True)
        return form_kwargs

    def check_for_session_based_redirects(self):
        errors = []
        if not self.session_data.get('counties', []):
            errors.append(
                NoCountiesInSessionError(
                    ("No counties in session data "
                     "on url %s for ip %s expires %s") %
                    (self.request.get_full_path(),
                     get_client_ip(
                        self.request),
                        self.request.session.get_expiry_date())))
        if not self.applicant:
            errors.append(
                NoApplicantInSessionError("No applicant in session data"))
        if errors:
            for error in errors:
                logger.error(error)
            return redirect(reverse('intake-apply'))

    def dispatch(self, request, *args, **kwargs):
        self.session_data = utils.get_form_data_from_session(
            request, self.session_key)
        self.applicant = \
            ApplicantsService.get_applicant_from_request_or_session(request)
        response = self.check_for_session_based_redirects()
        if response:
            return response
        self.county_slugs = self.session_data.getlist('counties', [])
        self.counties = models.County.objects.order_by_name_or_not_listed(
        ).filter(slug__in=self.county_slugs)
        self.formatted_county_names = [
            county.name for county in self.counties]
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            counties=self.counties,
            county_list=self.counties.values_list('name', flat=True))
        return context

    def log_page_completion_and_save_data(self, form):
        EventsService.form_page_complete(self)
        utils.save_form_data_to_session(
            self.request, self.session_key, form.data)

    def form_valid(self, form):
        self.log_page_completion_and_save_data(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        MessagesService.flash_errors(
            self.request, ERROR_MESSAGE, *form.non_field_errors())
        EventsService.form_validation_failed(
            self, errors=form.get_serialized_errors())

        return super().form_invalid(form)

    def get_receiving_organizations(self, form):
        if not getattr(self, 'receiving_organizations', None):
            self.receiving_organizations = [
                county.get_receiving_agency(form.cleaned_data)
                for county in self.counties]
        return self.receiving_organizations

    def finalize_application(self, form):
        organizations = self.get_receiving_organizations(form)
        submission = SubmissionsService.create_submission(
            form, organizations, self.applicant.id)
        EventsService.form_submitted(self, submission)
        SubmissionsService.send_to_newapps_bundle_if_needed(
            submission, organizations=organizations)
        sent_confirmations = \
            SubmissionsService.send_confirmation_notifications(submission)
        main_success_message = _(
            "You have applied for help in ") + oxford_comma(
                self.formatted_county_names)
        MessagesService.flash_success(
            self.request, main_success_message, *sent_confirmations)


def clear_form_session_data(request):
    utils.clear_session_data(
        request, ApplicantFormViewBase.session_key, 'applicant_id',
        'visitor_id')
