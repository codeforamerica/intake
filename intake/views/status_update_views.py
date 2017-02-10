from intake.forms import (
    StatusUpdateForm, StatusNotificationForm,
    NotificationContactInfoDisplayForm)
from intake import models, utils
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse

import intake.services.status_notifications as StatusNotificationService


class StatusUpdateBase:

    def get_session_storage_key(self):
        return 'status_update_form-{application_id}'.format(
           application_id=self.application.id)

    def get_status_update_from_session(self):
        querydict = utils.get_form_data_from_session(
            self.request, self.get_session_storage_key())
        form = StatusUpdateForm(querydict)
        form.is_valid()
        return form.cleaned_data

    def get_existing_form_data(self):
        return self.request.session.get(
            self.get_session_storage_key())

    def set_success_url(self):
        raise NotImplementedError('this must be overridden in a subclass')

    def dispatch(self, request, submission_id, *args, **kwargs):
        submission_id = int(submission_id)
        self.application = models.Application.objects.filter(
            form_submission=submission_id,
            organization=request.user.profile.organization).first()
        self.submission = models.FormSubmission.objects.get(
            id=submission_id)
        self.existing_status_update_data = \
            self.get_status_update_from_session()
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

    def get_initial(self):
        initial = super().get_initial()
        base_message = \
            StatusNotificationService.get_base_message_from_status_update_data(
                self.existing_status_update_data)
        initial.update(sent_message=base_message)
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        contact_info_display = NotificationContactInfoDisplayForm(
            self.submission.answers)
        intro_message = StatusNotificationService.get_notification_intro(
            self.request.user.profile)
        context.update(
            submission=self.submission,
            contact_info_display=contact_info_display,
            status_update=self.existing_status_update_data,
            intro_message=intro_message)
        return context

    def form_valid(self, form):
        StatusNotificationService.send_and_save_new_status(
            self.request,
            form.cleaned_data,
            self.existing_status_update_data)
        utils.clear_form_data_from_session(
            self.request, self.get_session_storage_key())
        return super().form_valid(form)


create_status_update = CreateStatusUpdateFormView.as_view()
review_status_notification = ReviewStatusNotificationFormView.as_view()
