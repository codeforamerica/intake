from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.views.generic import View
from django.views.generic.base import TemplateView

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse


from intake import models, notifications, permissions
from user_accounts.models import Organization
from printing.pdf_form_display import PDFFormDisplay
from intake.aggregate_serializer_fields import get_todays_date

import intake.services.submissions as SubmissionsService
import intake.services.bundles as BundlesService

NOT_ALLOWED_MESSAGE = str(
    "Sorry, you are not allowed to access that client information. "
    "If you have any questions, please contact us at "
    "clearmyrecord@codeforamerica.org")


def not_allowed(request):
    messages.error(request, NOT_ALLOWED_MESSAGE)
    return redirect('intake-app_index')


class ViewAppDetailsMixin(PermissionRequiredMixin):
    permission_required = permissions.CAN_SEE_APP_DETAILS.app_code


class ApplicationDetail(ViewAppDetailsMixin, View):
    """Displays detailed information for an org user.
    """
    template_name = "app_detail.jinja"

    def not_allowed(self, request):
        messages.error(request, NOT_ALLOWED_MESSAGE)
        return redirect('intake-app_index')

    def mark_viewed(self, request, submission):
        models.ApplicationLogEntry.log_opened([submission.id], request.user)
        notifications.slack_submissions_viewed.send(
            submissions=[submission], user=request.user,
            bundle_url=submission.get_external_url())

    def get(self, request, submission_id):
        if request.user.profile.should_see_pdf() and not request.user.is_staff:
            return redirect(
                reverse_lazy('intake-filled_pdf',
                             kwargs=dict(submission_id=submission_id)))
        submissions = list(SubmissionsService.get_permitted_submissions(
            request.user, [submission_id]))
        if not submissions:
            return self.not_allowed(request)
        submission = submissions[0]
        self.mark_viewed(request, submission)
        display_form, letter_display = submission.get_display_form_for_user(
            request.user)
        context = dict(
            form=display_form,
            declaration_form=letter_display)
        response = TemplateResponse(request, self.template_name, context)
        return response


class FilledPDF(ApplicationDetail):
    """Serves a filled PDF for an org user, based on the PDF
    needed by that user's organization.

    Deals with if a pdf doesn't exist but this shouldn't happen.
    Consider removing in favor of erroring and retrying on submission.
    """

    def get(self, request, submission_id):
        submission = get_object_or_404(
            models.FormSubmission, pk=int(submission_id))
        if not request.user.profile.should_have_access_to(submission):
            return self.not_allowed()
        pdf = submission.filled_pdfs.first()
        if not pdf:
            no_pdf_str = \
                "No prefilled pdf was made for submission: %s" % submission.pk
            notifications.slack_simple.send(no_pdf_str)
            fillables = models.FillablePDF.objects
            if not request.user.is_staff:
                org = request.user.profile.organization
                fillables = fillables.filter(
                    organization=org)
            fillable_pdf = fillables.first()
            pdf = fillable_pdf.fill_for_submission(submission)
        self.mark_viewed(request, submission)
        response = HttpResponse(pdf.pdf,
                                content_type='application/pdf')
        return response


class ApplicationIndex(ViewAppDetailsMixin, TemplateView):
    """A list view of all the application to a user's organization.
    """
    template_name = "app_index.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = list(
            SubmissionsService.get_permitted_submissions(
                self.request.user, related_objects=True))
        context['show_pdf'] = self.request.user.profile.should_see_pdf()
        context['body_class'] = 'admin'
        return context


class MultiSubmissionMixin:
    """A mixin for pulling multiple submission ids
    out of request query params.
    """

    def get_ids_from_params(self, request):
        id_set = request.GET.get('ids')
        return [int(i) for i in id_set.split(',')]

    def get_submissions_from_params(self, request):
        ids = self.get_ids_from_params(request)
        return list(SubmissionsService.get_permitted_submissions(
            request.user, ids))


class ApplicationBundle(ApplicationDetail, MultiSubmissionMixin):
    """A legacy view that should be deprecated

    Displays a set of submissions for an org user. These are typically
    new submissions, and the org user has followed a link from their email.
    """

    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = models.FormSubmission.objects.filter(
            pk__in=submission_ids)
        submissions = request.user.profile.filter_submissions(submissions)
        if len(submissions) < len(submission_ids):
            raise Http404(
                "Either those applications have been deleted or you don't "
                "have permission to view those applications")
        bundle = BundlesService\
            .get_or_create_for_submissions_and_user(submissions, request.user)
        forms = [
            submission.get_display_form_for_user(request.user)
            for submission in submissions]
        context = dict(
            bundle=bundle,
            forms=forms,
            count=len(submissions),
            show_pdf=request.user.profile.should_see_pdf(),
            app_ids=[sub.id for sub in submissions]
        )
        models.ApplicationLogEntry.log_bundle_opened(bundle, request.user)
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=request.user,
            bundle_url=bundle.get_external_url())
        return TemplateResponse(request, "app_bundle.jinja", context)


class ApplicationBundleDetail(ApplicationDetail):
    """New application bundle view which uses prerendered bundles

    Given a bundle id it returns a detail page for ApplicationBundle
    """
    def get(self, request, bundle_id):
        bundle = get_object_or_404(models.ApplicationBundle, pk=int(bundle_id))
        has_access = request.user.profile.should_have_access_to(bundle)
        if not has_access:
            return self.not_allowed(request)
        submissions = list(
            request.user.profile.filter_submissions(bundle.submissions.all()))
        forms = [
            submission.get_display_form_for_user(request.user)
            for submission in submissions]
        context = dict(
            bundle=bundle,
            forms=forms,
            count=len(submissions),
            show_pdf=bool(bundle.bundled_pdf),
            app_ids=[sub.id for sub in submissions],
            bundled_pdf_url=bundle.get_pdf_bundle_url())
        models.ApplicationLogEntry.log_bundle_opened(bundle, request.user)
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=request.user,
            bundle_url=bundle.get_external_url())
        return TemplateResponse(request, "app_bundle.jinja", context)


class ApplicationBundleDetailPDFView(ViewAppDetailsMixin, View):
    """A concatenated PDF of individual filled PDFs for an org user

    replaces FilledPDFBundle
    """
    def get(self, request, bundle_id):
        bundle = get_object_or_404(models.ApplicationBundle, pk=int(bundle_id))
        has_access = request.user.profile.should_have_access_to(bundle)
        if not bundle.bundled_pdf or not has_access:
            raise Http404(
                "There doesn't seem to be a PDF associated with these "
                "applications. If you think this is an error, please contact "
                "Code for America.")
        return HttpResponse(bundle.bundled_pdf, content_type="application/pdf")


def get_pdf_for_user(user, submission_data):
    """
    Creates a filled out pdf for a submission.

    TODO: remove
    """
    organization = user.profile.organization
    fillable = organization.pdfs.first()
    if isinstance(submission_data, list):
        return fillable.fill_many(submission_data)
    return fillable.fill(submission_data)


class FilledPDFBundle(FilledPDF, MultiSubmissionMixin):
    """A concatenated PDF of individual filled PDFs for an org user.
    Typically this is displayed in an iframe in `ApplicationBundle`
    """

    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = models.FormSubmission.objects.filter(
            pk__in=submission_ids)
        if not request.user.is_staff:
            submissions = submissions.filter(
                organizations__profiles=request.user.profile)
        if len(submissions) < len(submission_ids):
            raise Http404(
                "Either those applications have been deleted or you don't "
                "have permission to view those applications")
        bundle = BundlesService\
            .get_or_create_for_submissions_and_user(submissions, request.user)
        return redirect(bundle.get_pdf_bundle_url())


class Delete(ViewAppDetailsMixin, View):
    """A page to confirm the deletion of an individual application.
    """
    template_name = "delete_page.jinja"

    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        return TemplateResponse(
            request,
            self.template_name, {'submission': submission})

    def post(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        models.ApplicationLogEntry.objects.create(
            user=request.user,
            submission_id=submission_id,
            organization=request.user.profile.organization,
            event_type=models.ApplicationLogEntry.DELETED
        )
        submission.delete()
        notifications.slack_submissions_deleted.send(
            submissions=[submission],
            user=request.user)
        return redirect(reverse_lazy('intake-app_index'))


class MarkSubmissionStepView(ViewAppDetailsMixin, View, MultiSubmissionMixin):

    def modify_submissions(self):
        pass

    def get_organization_id(self):
        """Get the organization for logging this step.
        """
        return self.request.user.profile.organization.id

    def get_notification_context(self):
        return dict(
            submissions=self.submissions,
            user=self.request.user)

    def notify(self):
        pass

    def add_message(self):
        pass

    def log(self):
        models.ApplicationLogEntry.log_multiple(
            self.process_step,
            self.submission_ids,
            user=self.request.user,
            organization_id=self.get_organization_id())

    def get(self, request):
        self.request = request
        self.submissions = self.get_submissions_from_params(request)
        if not self.submissions:
            return not_allowed(request)

        self.submission_ids = [sub.id for sub in self.submissions]
        self.next_param = request.GET.get('next',
                                          reverse_lazy('intake-app_index'))
        self.log()
        self.modify_submissions()
        self.add_message()
        self.notify()
        return redirect(self.next_param)


class MarkProcessed(MarkSubmissionStepView):
    process_step = models.ApplicationLogEntry.PROCESSED

    def notify(self):
        notifications.slack_submissions_processed.send(
            **self.get_notification_context())


class ReferToAnotherOrgView(MarkSubmissionStepView):

    transfer_message_template = str(
        "You successfully transferred {applicant_name}'s application "
        "to {org_name}. You will no longer see their application."
    )

    def get_organization_id(self):
        return int(self.request.GET.get('to_organization_id'))

    def log(self):
        models.ApplicationLogEntry.log_referred_from_one_org_to_another(
            self.submission_ids[0],
            to_organization_id=self.get_organization_id(),
            user=self.request.user)

    def get_notification_context(self):
        return dict(
            submission=self.submissions[0],
            user=self.request.user)

    def modify_submissions(self):
        submission = self.submissions[0]
        to_organization_id = int(self.request.GET.get('to_organization_id'))
        submission.organizations.remove(
            self.request.user.profile.organization)
        submission.organizations.add(to_organization_id)

    def notify(self):
        notifications.slack_submission_transferred.send(
            **self.get_notification_context())

    def add_message(self):
        org = Organization.objects.get(pk=self.get_organization_id())
        message = self.transfer_message_template.format(
            org_name=org.name,
            applicant_name=self.submissions[0].get_full_name())
        messages.success(self.request, message)


def get_applicant_name(form):
    return '{}, {}'.format(
        form.last_name.get_display_value(),
        ' '.join([
                n for n in [
                    form.first_name.get_display_value(),
                    form.middle_name.get_display_value()
                ] if n
            ])
    )


def get_printout_for_submission(user, submission):
    # get the correct form
    form, letter = submission.get_display_form_for_user(user)
    # use the form to serialize the submission
    pdf_display = PDFFormDisplay(form, letter)
    canvas, pdf = pdf_display.render(
        title=get_applicant_name(form) + " - Case Details"
    )
    filename = '{}-{}-{}-CaseDetails.pdf'.format(
        form.last_name.get_display_value(),
        form.first_name.get_display_value(),
        submission.id
        )
    pdf.seek(0)
    return filename, pdf.read()


def get_concatenated_printout_for_bundle(user, bundle):
    # for each of the submissions,
    canvas = None
    pdf_file = None
    submissions = list(bundle.submissions.all())
    count = len(submissions)
    if count == 1:
        return get_printout_for_submission(user, submissions[0])
    for i, submission in enumerate(submissions):
        form, letter = submission.get_display_form_for_user(user)
        if i == 0:
            pdf_display = PDFFormDisplay(form, letter)
            canvas, pdf_file = pdf_display.render(save=False)
        elif i > 0 and i < (count - 1):
            pdf_display = PDFFormDisplay(form, letter, canvas=canvas)
            canvas, pdf = pdf_display.render(save=False)
        else:
            pdf_display = PDFFormDisplay(form, letter, canvas=canvas)
            canvas, pdf = pdf_display.render(
                save=True,
                title="{} Applications from Code for America".format(count))
    today = get_todays_date()
    filename = '{}-{}-Applications-CodeForAmerica.pdf'.format(
        today.strftime('%Y-%m-%d'),
        count
        )
    pdf_file.seek(0)
    return filename, pdf_file.read()


class CasePrintoutPDFView(ApplicationDetail):
    """Serves a PDF with full case details, based on the details
    needed by the user's organization

    The PDF is created on the fly
    """

    def get(self, request, submission_id):
        submission = get_object_or_404(
            models.FormSubmission, pk=int(submission_id))
        filename, pdf_bytes = get_printout_for_submission(
            request.user,
            submission)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response


class CaseBundlePrintoutPDFView(ViewAppDetailsMixin, View):
    """Returns a concatenated PDF of case detail PDFs
    for an org user
    """
    def get(self, request, bundle_id):
        bundle = get_object_or_404(
            models.ApplicationBundle,
            pk=int(bundle_id))
        filename, pdf_bytes = get_concatenated_printout_for_bundle(
            request.user, bundle)
        response = HttpResponse(
            pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response


filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
app_detail = ApplicationDetail.as_view()
mark_processed = MarkProcessed.as_view()
mark_transferred_to_other_org = ReferToAnotherOrgView.as_view()
delete_page = Delete.as_view()
app_bundle_detail = ApplicationBundleDetail.as_view()
app_bundle_detail_pdf = ApplicationBundleDetailPDFView.as_view()
case_printout = CasePrintoutPDFView.as_view()
case_bundle_printout = CaseBundlePrintoutPDFView.as_view()
