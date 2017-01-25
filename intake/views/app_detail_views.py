from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.contrib import messages
from django.template.response import TemplateResponse

import intake.services.submissions as SubmissionsService

from intake import models, notifications
from intake.views.base_views import ViewAppDetailsMixin

NOT_ALLOWED_MESSAGE = str(
    "Sorry, you are not allowed to access that client information. "
    "If you have any questions, please contact us at "
    "clearmyrecord@codeforamerica.org")


def not_allowed(request):
    messages.error(request, NOT_ALLOWED_MESSAGE)
    return redirect('intake-app_index')


class ApplicationDetail(ViewAppDetailsMixin, View):
    """Displays detailed information for an org user.
    """
    template_name = "app_detail.jinja"

    def not_allowed(self, request):
        messages.error(request, NOT_ALLOWED_MESSAGE)
        return redirect('intake-app_index')

    def mark_viewed(self, request, submission):
        models.ApplicationLogEntry.log_opened([submission.id], request.user)
        notifications.slack_submissions_viewed.send(
            submissions=[submission], user=request.user,
            bundle_url=submission.get_external_url())

    def get(self, request, submission_id):
        if request.user.profile.should_see_pdf() and not request.user.is_staff:
            return redirect(
                reverse_lazy('intake-filled_pdf',
                             kwargs=dict(submission_id=submission_id)))
        submissions = list(SubmissionsService.get_permitted_submissions(
            request.user, [submission_id]))
        if not submissions:
            return self.not_allowed(request)
        submission = submissions[0]
        self.mark_viewed(request, submission)
        display_form, letter_display = submission.get_display_form_for_user(
            request.user)
        context = dict(
            form=display_form,
            declaration_form=letter_display)
        response = TemplateResponse(request, self.template_name, context)
        return response

app_detail = ApplicationDetail.as_view()
