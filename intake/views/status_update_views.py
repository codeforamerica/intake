from intake.forms import StatusUpdateForm, StatusNotificationForm
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse_lazy


class CreateStatusUpdateFormView(FormView):
    template_name = 'create_status_update.jinja'
    form_class = StatusUpdateForm
    success_url = reverse_lazy('intake-review_status')


class ReviewStatusNotificationFormView(FormView):
    template_name = 'review_status_notification.jinja'
    form_class = StatusNotificationForm
    success_url = reverse_lazy('intake-app_index')
