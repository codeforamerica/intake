from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import TemplateView
from django.contrib import messages

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


class ApplicationDetail(ViewAppDetailsMixin, TemplateView):
    """Displays detailed information for an org user.
    """
    template_name = "app_detail.jinja"

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
        self.submissions = list(SubmissionsService.get_permitted_submissions(
            request.user, [submission_id]))
        if not self.submissions:
            return not_allowed(request)
        return super().get(request, submission_id)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        submission = self.submissions[0]
        self.mark_viewed(self.request, submission)
        display_form, letter_display = submission.get_display_form_for_user(
            self.request.user)
        application = models.Application.objects.filter(
            form_submission=submission,
            organization=self.request.user.profile.organization).first()
        if application.status_updates.exists():
            latest_status = application.status_updates.latest('updated')
        else:
            latest_status = None
        context.update(
            form=display_form,
            submission=submission,
            declaration_form=letter_display,
            latest_status=latest_status)
        return context


class ApplicationHistoryView(ApplicationDetail):
    """Displays a list of information abotu the history of this application
    """
    template_name = "app_history.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        org = self.request.user.profile.organization
        sub = context['submission']
        application = models.Application.objects.filter(
            organization=org, form_submission=sub).first()
        status_updates = models.StatusUpdate.objects.filter(
            application=application).prefetch_related('notification')
        context.update(
            org=org,
            application=application,
            status_updates=status_updates
            )
        return context


app_detail = ApplicationDetail.as_view()
app_history = ApplicationHistoryView.as_view()
