"""Views for processing multi-page intake forms and retrieving the session
data associated with them.
"""
import logging

from django.utils import timezone
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic.base import TemplateView

from intake.views import session_view_base as base_views
from formation.forms import (
    DeclarationLetterFormSpec, DeclarationLetterDisplay, SelectCountyForm)
from intake import models
from user_accounts.models import Organization

logger = logging.getLogger(__name__)


class Confirm(base_views.MultiCountyApplicationBase):
    """Intended to provide a final acceptance of a form,
    after any necessary warnings have been raised.
    It follows the `Apply` view, which checks for warnings.
    """
    incoming_message = _(str(
        "Please double check the form. "
        "Some parts are empty and may cause delays."))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        form_data = self.get_session_data()
        if form_data:
            form = self.get_form_class()(data=form_data)
            # make sure the form has warnings.
            # trigger data cleaning
            form.is_valid()
            if form.warnings:
                messages.warning(self.request, self.incoming_message)
            context['form'] = form
        return context

    def form_valid(self, form):
        self.log_page_complete()
        return super().form_valid(form)


class CountyApplication(base_views.MultiCountyApplicationBase):
    """The initial application page.
    Checks for warnings, and if they exist, redirects to a confirmation page.
    """
    confirmation_url = reverse_lazy('intake-confirm')

    def form_valid(self, form):
        """If no errors, check for warnings, redirect to confirmation if needed
        """
        self.log_page_complete()
        if form.warnings:
            # save the post data and move them to confirmation step
            self.update_session_data(**form.parsed_data)
            return redirect(self.confirmation_url)
        else:
            return super().form_valid(form)


class DeclarationLetterView(base_views.MultiCountyApplicationBase):
    template_name = "forms/declaration_letter_form.jinja"

    form_spec = DeclarationLetterFormSpec()

    def redirect_if_no_session_data(self):
        # TODO: refactor to not check form validity twice, don't grab the
        # session data too many times
        data = self.get_session_data()
        if not data:
            logger.warn(
                "{} hit with no existing session data".format(
                    self.__class__.__name__))
            return True, data, redirect(reverse('intake-apply'))
        else:
            return False, data, None

    def get(self, request):
        should_redirect, data, response = self.redirect_if_no_session_data()
        if should_redirect:
            return response
        return super().get(request)

    def get_form_class(self):
        return self.form_spec.build_form_class()

    def form_valid(self, declaration_letter_form):
        """If valid, redirect to a page to review the letter
        """
        self.log_page_complete()
        self.update_session_data(
            **declaration_letter_form.cleaned_data)
        return redirect(reverse('intake-review_letter'))


class DeclarationLetterReviewPage(DeclarationLetterView):
    template_name = "forms/declaration_letter_review.jinja"

    def get(self, request):
        """Diverts from super().get() to return a display only form
        rather than the declaration letter form
        """
        should_redirect, data, response = self.redirect_if_no_session_data()
        if should_redirect:
            return response
        data['date_received'] = timezone.now()
        display_form = DeclarationLetterDisplay(data)
        display_form.display_only = True
        display_form.is_valid()
        context = dict(form=display_form)
        return render(request, self.template_name, context)

    def get_form_kwargs(self):
        """Pull in form data from the session
        """
        return dict(data=self.get_session_data())

    def post(self, request):
        should_redirect, data, response = self.redirect_if_no_session_data()
        if should_redirect:
            return response
        decision = request.POST.get("submit_action")
        if decision == "edit_letter":
            return redirect(reverse('intake-write_letter'))
        elif decision == "approve_letter":
            BaseCountyFormSpec = super().get_form_specs()
        Form = (
            self.form_spec | BaseCountyFormSpec
        ).build_form_class()
        form = Form(data)
        form.is_valid()
        self.log_page_complete()
        self.save_submission_and_send_notifications(form)
        return base_views.MultiStepFormViewBase.form_valid(self, form)


class SelectCounty(base_views.MultiStepFormViewBase):
    """A page where users select the counties they'd like help with.

    The user's county selection is stored in the session.
    """
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def post(self, request):
        self.applicant_id = self.get_or_create_applicant_id()
        return super().post(request)

    def form_valid(self, form):
        self.update_session_data(**form.parsed_data)
        models.ApplicationEvent.log_app_started(
            self.get_applicant_id(),
            counties=form.parsed_data['counties'],
            referrer=self.request.session.get('referrer'),
            ip=self.request.ip_address,
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            )
        return super().form_valid(form)


def get_last_submission_of_applicant(applicant_id):
    return models.FormSubmission.objects.filter(
        applicant_id=applicant_id).latest('date_received')


class Thanks(TemplateView, base_views.GetFormSessionDataMixin):
    """A confirmation page that shows flash messages and next steps for a
    user.
    """
    template_name = "thanks.jinja"

    def get(self, request):
        self.applicant_id = self.get_applicant_id()
        if not self.applicant_id:
            return redirect(reverse('intake-home'))
        return super().get(request)

    def get_context_data(self, *args, **kwargs):
        sub = get_last_submission_of_applicant(self.applicant_id)
        context = dict(
            organizations=sub.organizations.all()
            )
        return context


class RAPSheetInstructions(TemplateView, base_views.GetFormSessionDataMixin):
    template_name = "rap_sheet_instructions.jinja"

    def get_context_data(self, *args, **kwargs):
        context = {}
        applicant_id = self.get_applicant_id()
        if applicant_id:
            submission = get_last_submission_of_applicant(applicant_id)
            context['organizations'] = submission.organizations.all()
            context['qualifies_for_fee_waiver'] = \
                submission.qualifies_for_fee_waiver()
        return context


select_county = SelectCounty.as_view()
county_application = CountyApplication.as_view()
confirm = Confirm.as_view()
write_letter = DeclarationLetterView.as_view()
review_letter = DeclarationLetterReviewPage.as_view()
thanks = Thanks.as_view()
rap_sheet_info = RAPSheetInstructions.as_view()
