from intake.forms import StatusUpdateForm, StatusNotificationForm
from intake import models
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy


class CreateStatusUpdateFormView(FormView):
    template_name = 'create_status_update.jinja'
    form_class = StatusUpdateForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            application=self.application,
            author=self.request.user
            )
        return initial

    def dispatch(self, request, submission_id, *args, **kwargs):
        self.application = models.Application.objects.filter(
            form_submission=int(submission_id),
            organization=request.user.profile.organization).first()
        self.submission = models.FormSubmission.objects.get(
            id=int(submission_id))
        self.success_url = reverse(
            'intake-review_status_notification',
            kwargs=dict(submission_id=submission_id))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            application=self.application,
            submission=self.submission
            )
        return context

    def form_valid(self, form):
        status_update = form.save()
        import ipdb; ipdb.set_trace()
        return super().form_valid(form)


class ReviewStatusNotificationFormView(FormView):
    template_name = 'review_status_notification.jinja'
    form_class = StatusNotificationForm
    success_url = reverse_lazy('intake-app_index')


create_status_update = CreateStatusUpdateFormView.as_view()
review_status_notification = ReviewStatusNotificationFormView.as_view()
