from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.contrib import messages
import intake.services.submissions as SubmissionsService
import intake.services.applications_service as AppsService
import intake.services.display_form_service as DisplayFormService
from intake import models
from intake.views.base_views import ViewAppDetailsMixin, not_allowed


class ApplicationDetail(ViewAppDetailsMixin, TemplateView):
    """Displays detailed information for an org user.
    """
    template_name = "app_detail.jinja"

    marked_read_flash_message = str(
        "{applicant_name}'s application has been marked \"Read\" and moved to "
        "the \"Needs Status Update\" folder.")

    def get(self, request, submission_id):
        self.submissions = list(SubmissionsService.get_permitted_submissions(
            request.user, [submission_id]))
        if not self.submissions:
            return not_allowed(request)
        return super().get(request, submission_id)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        self.submission = self.submissions[0]
        display_form, letter_display = \
            DisplayFormService.get_display_form_for_user_and_submission(
                self.request.user, self.submission)
        applications = models.Application.objects.filter(
            form_submission=self.submission)
        if not self.request.user.is_staff:
            applications = applications.filter(
                organization=self.request.user.profile.organization)
            application = applications.first()
            if not application.has_been_opened:
                message = self.marked_read_flash_message.format(
                    applicant_name=self.submission.get_full_name())
                messages.success(self.request, message)
        for application in applications:
            if application.status_updates.exists():
                # latest_status is cached on the model instance
                # for easier template randering. It is not saved to the db
                application.latest_status = \
                    application.status_updates.latest('updated')
        context.update(
            form=display_form,
            submission=self.submission,
            declaration_form=letter_display,
            applications=applications,
            should_see_pdf=self.request.user.profile.should_see_pdf())
        AppsService.handle_apps_opened(self, applications)
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
