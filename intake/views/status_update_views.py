from intake.forms import (
    StatusUpdateForm, StatusNotificationForm,
    NotificationContactInfoDisplayForm)
from intake import models, utils
from django.views.generic.edit import FormView
from django.urls import reverse
from django.shortcuts import redirect
from intake.views.base_views import not_allowed
import intake.services.events_service as EventsService
import intake.services.status_notifications as StatusNotificationService


WARNING_MESSAGE = str(
    "This applicant has opted out of email and text messages"
    " from Clear My Record, so we won't send them a message.")


class StatusUpdateBase:

    def set_request_scoping_properties(self, request, submission_id, **kwargs):
        self.request = request
        submission_id = int(submission_id)
        self.application = models.Application.objects.filter(
            form_submission=submission_id,
            organization=request.user.profile.organization).first()
        if self.application:
            self.application.latest_status = \
                models.StatusUpdate.objects.filter(
                    application_id=self.application.id
                ).order_by('-created').first()
        self.submission = models.FormSubmission.objects.filter(
            id=submission_id).first()

    def get_session_storage_key(self):
        return 'status_update_form-{application_id}'.format(
            application_id=self.application.id)

    def get_status_update_from_session(self):
        querydict = utils.get_form_data_from_session(
            self.request, self.get_session_storage_key())
        form = StatusUpdateForm(querydict)
        form.is_valid()
        return form.cleaned_data

    def check_for_scope_based_redirects(self):
        """Override in child classes to redirect requests based on instance
        properties.
        """
        if not self.application:
            return not_allowed(self.request)

    def check_for_session_based_redirects(self):
        """Override in child classes to redirect requests based on session
        content
        """
        return None

    def get_existing_form_data(self):
        return self.request.session.get(
            self.get_session_storage_key())

    def set_success_url(self):
        raise NotImplementedError('this must be overridden in a subclass')

    def dispatch(self, request, submission_id, *args, **kwargs):
        """
        Override of dispatch for special cases. Includes hooks to check for
        object permission and session data (to indicate access). Handles
        accordingly.
        """
        self.set_request_scoping_properties(
            request, submission_id, *args, **kwargs)
        response = self.check_for_scope_based_redirects()
        if response:
            return response
        self.existing_status_update_data = \
            self.get_status_update_from_session()
        response = self.check_for_session_based_redirects()
        if response:
            return response
        self.set_success_url()
        return super().dispatch(request, *args, **kwargs)


class CreateStatusUpdateFormView(StatusUpdateBase, FormView):
    template_name = 'create_status_update.jinja'
    form_class = StatusUpdateForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.existing_status_update_data)
        initial.update(
            application=self.application,
            author=self.request.user,
        )
        return initial

    def set_success_url(self):
        self.success_url = reverse(
            'intake-review_status_notification',
            kwargs=dict(submission_id=self.submission.id))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            application=self.application,
            submission=self.submission)
        return context

    def form_valid(self, form):
        utils.save_form_data_to_session(
            self.request, self.get_session_storage_key(), form.data)
        return super().form_valid(form)


class ReviewStatusNotificationFormView(StatusUpdateBase, FormView):
    template_name = 'review_status_notification.jinja'
    form_class = StatusNotificationForm

    def set_success_url(self):
        self.success_url = reverse('intake-app_index')

    def check_for_session_based_redirects(self):
        """Checks if the session was cleared, if so, redirects to create status
        page.
        """
        if 'application' not in self.existing_status_update_data:
            return redirect(reverse(
                'intake-create_status_update',
                kwargs=dict(submission_id=self.submission.id)))

    def get_initial(self):
        initial = super().get_initial()
        base_message = \
            StatusNotificationService.get_base_message_from_status_update_data(
                self.request,
                self.existing_status_update_data)
        initial.update(sent_message=base_message)
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        intro_message = StatusNotificationService.get_notification_intro(
            self.request.user.profile)
        usable_contact_info = self.submission.get_usable_contact_info()
        all_contact_info_display = NotificationContactInfoDisplayForm(
            self.submission.answers)
        context.update(
            submission=self.submission,
            contact_info=self.submission.get_contact_info(),
            usable_contact_info=usable_contact_info,
            all_contact_info_display_form=all_contact_info_display,
            status_update=self.existing_status_update_data,
            intro_message=intro_message,
            WARNING_MESSAGE=WARNING_MESSAGE,
            warning=WARNING_MESSAGE if not usable_contact_info else "")
        return context

    def form_valid(self, form):
        status_update = StatusNotificationService.send_and_save_new_status(
            self.request,
            form.cleaned_data,
            self.existing_status_update_data)
        EventsService.status_updated(self, status_update)
        EventsService.user_status_updated(self, status_update)
        utils.clear_form_data_from_session(
            self.request, self.get_session_storage_key())
        return super().form_valid(form)


create_status_update = CreateStatusUpdateFormView.as_view()
review_status_notification = ReviewStatusNotificationFormView.as_view()
