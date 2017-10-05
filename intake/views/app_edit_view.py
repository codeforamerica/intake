from django.views.generic.edit import UpdateView

from intake.models import FormSubmission
from intake.services.edit_form_service import \
    get_edit_form_class_for_user_and_submission


class AppEditView(UpdateView):
    model = FormSubmission
    template_name = "app_edit.jinja"
    pk_url_kwarg = 'submission_id'
    fields = ['first_name', 'last_name']

    def get_success_url(self):
        return self.submission.get_absolute_url()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        self.submission = obj
        return obj

    def get_form_class(self):
        return get_edit_form_class_for_user_and_submission(self.request.user,
                                                           self.submission)

    def get_form_kwargs(self):
        return {'data': self.submission.answers}

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.model.objects.all()

        return self.model.objects.filter(
            organizations__profiles__user=self.request.user)


app_edit = AppEditView.as_view()
