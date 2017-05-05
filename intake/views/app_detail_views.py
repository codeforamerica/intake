from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import TemplateView
from django.contrib import messages
import intake.services.submissions as SubmissionsService
import intake.services.applications_service as AppsService
from intake import models
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
        display_form, letter_display = submission.get_display_form_for_user(
            self.request.user)
        applications = models.Application.objects.filter(
            form_submission=submission)
        if not self.request.user.is_staff:
            applications = applications.filter(
                organization=self.request.user.profile.organization)
        for application in applications:
            if application.status_updates.exists():
                # latest_status is cached on the model instance
                # for easier template randering. It is not saved to the db
                application.latest_status = \
                    application.status_updates.latest('updated')
        context.update(
            form=display_form,
            submission=submission,
            declaration_form=letter_display,
            applications=applications)
        SubmissionsService.mark_opened(submission, self.request.user)
        return context


class ApplicationHistoryView(ApplicationDetail):
    """Displays a list of information abotu the history of this application
    """
    template_name = "app_history.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        apps = context['applications']
        status_updates = \
            AppsService.get_serialized_application_history_events(
                apps[0], self.request.user)
        context.update(status_updates=status_updates)
        return context


app_detail = ApplicationDetail.as_view()
app_history = ApplicationHistoryView.as_view()
