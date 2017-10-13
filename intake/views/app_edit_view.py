from django.views.generic.edit import UpdateView
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from intake.models import FormSubmission
from intake.services.edit_form_service import (
    get_edit_form_class_for_user_and_submission,
    SENSITIVE_FIELD_LABELS,
    get_changed_data_from_form
)
from intake.notifications import app_edited_email_notification
from intake.services.submissions import update_submission_answers
from intake.services.messages_service import flash_success


def remove_sensitive_data_from_data_diff(unsafe_data_diff):
    """Removes 'before' and 'after' data for fields that are sensitive, such
    as social security number and driver's license number
    """
    safe_data_diff = {}
    unsafe_changed_keys = []
    for label, values in unsafe_data_diff.items():
        if label not in SENSITIVE_FIELD_LABELS:
            safe_data_diff[label] = values
        else:
            unsafe_changed_keys.append(label)
    return safe_data_diff, unsafe_changed_keys


def get_emails_to_notify_of_edits(form_submission_id):
    return User.objects.filter(
            profile__should_get_notifications=True,
            profile__organization__submissions__id=form_submission_id
        ).values_list('email', flat=True)


class AppEditView(UpdateView):
    model = FormSubmission
    template_name = "app_edit.jinja"
    pk_url_kwarg = 'submission_id'
    context_object_name = 'submission'

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
                'validate': True}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        existing_data_form = context['form'].__class__(
            self.submission.answers, validate=True)
        context['existing_data_form'] = existing_data_form
        return context

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.model.objects.all()

        return self.model.objects.filter(
            organizations__profiles__user=self.request.user)

    def form_valid(self, form):
        unsafe_data_diff = get_changed_data_from_form(form)
        if unsafe_data_diff:
            update_submission_answers(self.submission, form.cleaned_data)
            flash_success(
                self.request,
                'Saved new information for {}'.format(
                    self.submission.get_full_name()))
            safe_data_diff, unsafe_diff_keys = \
                remove_sensitive_data_from_data_diff(unsafe_data_diff)
            notifiable_emails = get_emails_to_notify_of_edits(
                self.submission.id)
            org_name = self.request.user.profile.organization.name
            for to_email in notifiable_emails:
                app_edited_email_notification.send(
                    to=[to_email],
                    editor_email=self.request.user.email,
                    editor_org_name=org_name,
                    app_detail_url=self.submission.get_external_url(),
                    submission_id=self.submission.id,
                    applicant_name=self.submission.get_full_name(),
                    safe_data_diff=safe_data_diff,
                    unsafe_changed_keys=unsafe_diff_keys)
        return HttpResponseRedirect(self.get_success_url())


app_edit = AppEditView.as_view()
