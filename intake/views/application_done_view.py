from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.base import TemplateView
from .applicant_form_view_base import clear_form_session_data
import intake.services.submissions as SubmissionsService
import intake.services.applicants as ApplicantsService


class ThanksView(TemplateView):
    template_name = "thanks.jinja"

    def dispatch(self, request, *args, **kwargs):
        applicant = ApplicantsService.get_applicant_from_request_or_session(
            request)
        if not applicant:
            return redirect(reverse('intake-home'))
        self.submission = \
            SubmissionsService.get_latest_submission_from_applicant(
                applicant.id)
        if not self.submission:
            return redirect(reverse('intake-home'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            organizations=self.submission.organizations.not_cfa(),
            unlisted_counties=self.submission.answers.get(
                'unlisted_counties', ''))
        clear_form_session_data(self.request)
        return context


class RAPSheetInstructionsView(TemplateView):
    template_name = "rap_sheet_instructions.jinja"

    def get_context_data(self):
        context = super().get_context_data()
        applicant = ApplicantsService.get_applicant_from_request_or_session(
            self.request)
        if applicant:
            submission = \
                SubmissionsService.get_latest_submission_from_applicant(
                    applicant.id)
            if submission:
                context['organizations'] = submission.organizations.not_cfa()
                context['qualifies_for_fee_waiver'] = \
                    SubmissionsService.qualifies_for_fee_waiver(submission)
            clear_form_session_data(self.request)
        return context


thanks = ThanksView.as_view()
rap_sheet_info = RAPSheetInstructionsView.as_view()
