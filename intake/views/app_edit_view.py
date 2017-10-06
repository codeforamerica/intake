from django.views.generic.edit import UpdateView
from django.http import HttpResponseRedirect
from intake.models import FormSubmission
from intake.services.edit_form_service import (
    get_edit_form_class_for_user_and_submission,
    has_errors_on_existing_data_only,
    remove_errors_for_existing_data)
from intake.services.submissions import update_submission_answers
from intake.services.messages_service import flash_success


class AppEditView(UpdateView):
    model = FormSubmission
    template_name = "app_edit.jinja"
    pk_url_kwarg = 'submission_id'
    context_object_name = 'submission'
    fields = ['first_name', 'last_name']

    def get_success_url(self):
        return self.submission.get_absolute_url()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        self.submission = obj
        return obj

    def get_form_class(self):
        return get_edit_form_class_for_user_and_submission(
            self.request.user, self.submission)

    def get_form_kwargs(self):
        if self.request.method in ('POST', 'PUT'):
            kwargs = {
                'data': self.request.POST}
        else:
            kwargs = {
                'data': self.submission.answers,
                'validate': True,
                'skip_validation_parse_only': True}
        return kwargs

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.model.objects.all()

        return self.model.objects.filter(
            organizations__profiles__user=self.request.user)

    def form_invalid(self, form):
        # ignore and remove errors for data that was unchanged
        if has_errors_on_existing_data_only(form, self.submission):
            return self.form_valid(form)
        else:
            remove_errors_for_existing_data(form, self.submission)
            return super().form_invalid(form)

    def form_valid(self, form):
        update_submission_answers(self.submission, form.cleaned_data)
        flash_success(
            self.request,
            'Saved new information for {}'.format(
                self.submission.get_full_name()))
        return HttpResponseRedirect(self.get_success_url())


app_edit = AppEditView.as_view()
