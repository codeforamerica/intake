from intake.forms import ApplicationTransferForm
from intake import models
from django.contrib import messages
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
import intake.services.transfers_service as TransferService
from django.shortcuts import redirect
from intake.views.base_views import not_allowed


class ApplicationTransferView(FormView):
    template_name = "transfer_application.jinja"
    form_class = ApplicationTransferForm

    transfer_success_flash_message = str(
        "You successfully transferred {applicant_name}'s application "
        "to {to_organization}.")

    def dispatch(self, request, submission_id, *args, **kwargs):
        self.next_url = request.GET.get(
            'next', reverse_lazy('intake-app_index'))
        self.author = request.user
        self.from_organization = request.user.profile.organization
        self.to_organization = \
            request.user.profile.organization.transfer_partners.first()
        submission_id = int(submission_id)
        self.submission = models.FormSubmission.objects.get(
            id=submission_id)
        self.application = self.submission.applications.filter(
            organization=self.from_organization).first()
        if not self.to_organization or not self.application:
            return not_allowed(request)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        intro, body = TransferService.render_application_transfer_message(
            form_submission=self.submission,
            author=self.author,
            to_organization=self.to_organization,
            from_organization=self.from_organization)
        self.message_intro = intro
        initial.update(
            to_organization=self.to_organization,
            sent_message=body,
            next_url=self.next_url)
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['form'].fields['to_organization'].queryset = \
            self.from_organization.transfer_partners.all()
        usable_contact_info = self.submission.get_usable_contact_info()
        context.update(
            submission=self.submission,
            intro_message=self.message_intro,
            usable_contact_info=usable_contact_info)
        return context

    def form_valid(self, form):
        transfer_data = form.cleaned_data
        next_url = transfer_data.pop('next_url', '')
        if not next_url:
            next_url = self.next_url
        transfer_data = form.cleaned_data
        transfer_data.update(
            author=self.author, application=self.application,
            form_submission=self.submission,
            from_organization=self.from_organization)
        TransferService.transfer_application_and_notify_applicant(
            transfer_data)
        message = self.transfer_success_flash_message.format(
            to_organization=self.to_organization.name,
            applicant_name=self.submission.get_full_name())
        messages.success(self.request, message)
        return redirect(next_url)


transfer_application = ApplicationTransferView.as_view()
