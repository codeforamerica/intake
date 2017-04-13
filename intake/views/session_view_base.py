"""Base classes for views that access session data and process intake forms
"""

import logging
import json

from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic.edit import FormView

from project.jinja2 import oxford_comma
from intake import models, notifications
from user_accounts.models import Organization
from formation.forms import county_form_selector

import intake.services.submissions as SubmissionsService
from intake.exceptions import NoCountyCookiesError


logger = logging.getLogger(__name__)


GENERIC_USER_ERROR_MESSAGE = _(
    "Oops! Something went wrong. This is embarrassing. If you noticed anything"
    " unusual, please email us: clearmyrecord@codeforamerica.org")


class GetFormSessionDataMixin:
    """Responsible for retreiving form data stored in a session.

    This adds methods for getting session data, but not for setting it
    """
    session_storage_key = "form_in_progress"

    def check_session_data_validity(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        """Wrap super().dispatch to catch and handle errors
        """
        self.session_data = self.get_session_data()
        try:
            self.check_session_data_validity()
        except NoCountyCookiesError as err:
            logger.error(err)
            return redirect(reverse('intake-apply'))
        return super().dispatch(request, *args, **kwargs)

    def get_session_data(self):
        return dict(**self.request.session.get(self.session_storage_key, {}))

    def clear_session_data(self, *keys):
        existing_keys = list(self.request.session.keys())
        for key_to_delete in [self.session_storage_key, *keys]:
            if key_to_delete in existing_keys:
                del self.request.session[key_to_delete]

    def get_counties(self):
        session_data = self.get_session_data()
        county_slugs = session_data.get('counties', [])
        return models.County.objects.filter(slug__in=county_slugs).all()

    def get_organizations(self):
        org_slugs = self.get_session_data().get('organizations', [])
        return Organization.objects.filter(slug__in=org_slugs)

    def get_county_context(self):
        counties = self.get_counties()
        return dict(
            counties=counties,
            county_list=[county.name + " County" for county in counties]
        )

    def get_applicant_id(self):
        return getattr(self, 'applicant_id', None) \
            or self.request.session.get('applicant_id')


class MultiStepFormViewBase(GetFormSessionDataMixin, FormView):
    """A FormView saves form data in a session for persistence between URLs.
    """
    ERROR_MESSAGE = _(str(
        "There were some problems with your application. "
        "Please check the errors below."))

    def update_session_data(self, **data):
        form_data = self.request.session.get(self.session_storage_key, {})
        if data:
            form_data.update(data)
        self.request.session[self.session_storage_key] = form_data
        return form_data

    def put_errors_in_flash_messages(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, self.ERROR_MESSAGE)
        self.put_errors_in_flash_messages(form)
        models.ApplicationEvent.log_app_errors(
            self.get_applicant_id(),
            errors=form.get_serialized_errors())
        return super().form_invalid(form, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        # adds the form and form class
        context = super().get_context_data(*args, **kwargs)
        context.update(self.get_county_context())
        return context

    def get_or_create_applicant_id(self, visitor_id=None):
        applicant_id = self.get_applicant_id()
        if not applicant_id:
            applicant = models.Applicant(visitor_id=visitor_id)
            applicant.save()
            applicant_id = applicant.id
            self.request.session['applicant_id'] = applicant.id
        self.applicant_id = applicant_id
        return applicant_id


class MultiCountyApplicationBase(MultiStepFormViewBase):
    """A multi-page dynamic form view based on data stored in the session.

    The form class is created dynamically based on data stored in the session.
    Once created, the form class is fed POST data from the session.
    """
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')
    form_spec = None

    def check_session_data_validity(self):
        counties = self.session_data.get('counties', [])
        if not counties:
            error_data = dict(
                referrer=self.request.session.get('referrer', None),
                path=self.request.path,
                user_agent=self.request.META.get('HTTP_USER_AGENT', 'None'),
                session_data=dict([
                    keyval for keyval in self.request.session.items()]),
            )
            error_message = "No Counties in session data: `{}`".format(
                json.dumps(error_data))
            raise NoCountyCookiesError(error_message)

    def get_form(self, *args):
        if self.form_spec:
            form_class_specification = self.form_spec
        else:
            county_slugs = self.session_data.get('counties', [])
            form_class_specification = \
                county_form_selector.get_combined_form_spec(
                    counties=county_slugs)
        CombinedFormClass = form_class_specification.build_form_class()
        if self.request.method in ('POST', 'PUT'):
            return CombinedFormClass(data=self.request.POST)
        elif self.request.method == 'GET':
            form_input_keys = set(CombinedFormClass.get_field_keys())
            session_data_keys = set(self.session_data.keys())
            session_and_form_overlap = \
                session_data_keys & form_input_keys
            if session_and_form_overlap:
                return CombinedFormClass(data=self.session_data, validate=True)
            else:
                # we have a new empty form with no saved session
                return CombinedFormClass()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        county_slugs = self.session_data.get('counties', [])
        counties = models.County.objects.filter(slug__in=county_slugs).all()
        context.update(
            counties=counties,
            county_list=[county.name + " County" for county in counties])
        return context

    def create_confirmations_for_user(self, submission):
        """Sends texts/emails to user and adds flash messages
        """
        county_list = [
            name + " County" for name in submission.get_nice_counties()]
        joined_county_list = oxford_comma(county_list)
        full_message = _("You have applied for help in ") + joined_county_list
        messages.success(self.request, full_message)
        # send emails and texts
        sent_confirmations = \
            SubmissionsService.send_confirmation_notifications(submission)
        for message in sent_confirmations:
            messages.success(self.request, message)

    def get_orgs_for_answers(self, answers):
        counties = self.get_counties()
        return [
            county.get_receiving_agency(answers)
            for county in counties]

    def save_submission(self, form, organizations):
        """Save the submission data
        """
        applicant_id = self.get_applicant_id()
        submission = models.FormSubmission(
            answers=form.cleaned_data,
            applicant_id=applicant_id)
        submission.save()
        submission.organizations.add(*organizations)
        models.ApplicationEvent.log_app_submitted(applicant_id)
        # TODO: check for cerrect org in view tests
        return submission

    def send_notifications(self, submission):
        number = models.FormSubmission.objects.count()
        # TODO: say which orgs this is going to in notification
        notifications.slack_new_submission.send(
            submission=submission, request=self.request,
            submission_count=number)
        self.create_confirmations_for_user(submission)

    def save_submission_and_send_notifications(self, form):
        organizations = self.get_orgs_for_answers(form.cleaned_data)
        submission = SubmissionsService.create_submission(
            form,
            organizations,
            self.get_applicant_id())
        self.send_notifications(submission)

    def form_valid(self, form):
        # if for alameda, send to declaration letter
        organizations = self.get_orgs_for_answers(form.cleaned_data)
        self.update_session_data(
            organizations=[org.slug for org in organizations],
            **form.parsed_data)
        if any([org.requires_declaration_letter for org in organizations]):
            return redirect(reverse('intake-write_letter'))
        submission = SubmissionsService.create_submission(
            form,
            organizations,
            self.get_applicant_id())
        self.send_notifications(submission)
        SubmissionsService.fill_pdfs_for_submission(submission)
        if any([org.requires_rap_sheet for org in organizations]):
            return redirect(reverse('intake-rap_sheet'))
        return super().form_valid(form)

    def log_page_complete(self):
        return models.ApplicationEvent.log_page_complete(
            applicant_id=self.get_applicant_id(),
            page_name=self.__class__.__name__)
