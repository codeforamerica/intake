from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.views.generic import View
from django.views.generic.base import TemplateView

from django.db.models import Q

from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse

from dal import autocomplete


from intake import models, notifications, forms, utils
from printing.pdf_form_display import PDFFormDisplay

import intake.services.submissions as SubmissionsService
import intake.services.applications_service as AppsService
import intake.services.bundles as BundlesService
import intake.services.tags as TagsService

from intake.views.base_views import ViewAppDetailsMixin
from intake.views.app_detail_views import ApplicationDetail, not_allowed


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
        SubmissionsService.mark_opened(submission, request.user)
        response = HttpResponse(pdf.pdf,
                                content_type='application/pdf')
        return response


class ApplicationIndex(ViewAppDetailsMixin, TemplateView):
    """A paginated list view of all the applications to a user's organization.
    """
    template_name = "app_index.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_staff = self.request.user.is_staff
        context['show_pdf'] = self.request.user.profile.should_see_pdf()
        context['body_class'] = 'admin'
        context['search_form'] = forms.ApplicationSelectForm()
        if is_staff:
            context['ALL_TAG_NAMES'] = TagsService.get_all_used_tag_names()
            context['results'] = \
                SubmissionsService.get_submissions_for_followups()
        else:
            context['results'] = \
                AppsService.get_applications_index_for_org_user(
                    self.request.user, self.request.GET.get('page'))
            context['page_counter'] = \
                utils.get_page_navigation_counter(
                    page=context['results'],
                    wing_size=9)
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
        BundlesService.mark_opened(bundle, request.user)
        return TemplateResponse(request, "app_bundle.jinja", context)


class ApplicationBundleDetail(ApplicationDetail):
    """New application bundle view which uses prerendered bundles

    Given a bundle id it returns a detail page for ApplicationBundle
    """

    def get(self, request, bundle_id):
        bundle = get_object_or_404(models.ApplicationBundle, pk=int(bundle_id))
        has_access = request.user.profile.should_have_access_to(bundle)
        if not has_access:
            return not_allowed(request)
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
        BundlesService.mark_opened(bundle, request.user)
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
        BundlesService.mark_opened(bundle, request.user)
        return HttpResponse(bundle.bundled_pdf, content_type="application/pdf")


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
    today = utils.get_todays_date()
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
        if not submission.organizations.filter(
                id=request.user.profile.organization_id).exists():
            return not_allowed(request)
        SubmissionsService.mark_opened(
            submission, request.user, send_slack_notification=False)
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
        if bundle.organization_id != request.user.profile.organization_id:
            return not_allowed(request)
        BundlesService.mark_opened(
            bundle, request.user, send_slack_notification=False)
        filename, pdf_bytes = get_concatenated_printout_for_bundle(
            request.user, bundle)
        response = HttpResponse(
            pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response


class ApplicantAutocomplete(autocomplete.Select2QuerySetView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponse(status=403)

    def get_queryset(self):
        if self.request.user.is_staff:
            qs = qs = models.Application.objects.all()
        else:
            qs = models.Application.objects.filter(
                organization=self.request.user.profile.organization)

        if self.q:
            qs = qs.filter(
                Q(form_submission__first_name__icontains=self.q) |
                Q(form_submission__last_name__icontains=self.q) |
                Q(form_submission__ssn__icontains=self.q) |
                Q(form_submission__last_four__icontains=self.q) |
                Q(form_submission__drivers_license_or_id__icontains=self.q) |
                Q(form_submission__phone_number__icontains=self.q) |
                Q(form_submission__alternate_phone_number__icontains=self.q) |
                Q(form_submission__email__icontains=self.q) |
                Q(form_submission__case_number__icontains=self.q)
            )
        return qs

    def get_result_value(self, application):
        return dict(
            organization=application.organization.name,
            name=application.form_submission.get_full_name(),
            url=application.form_submission.get_absolute_url())


filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
mark_processed = MarkProcessed.as_view()
app_bundle_detail = ApplicationBundleDetail.as_view()
app_bundle_detail_pdf = ApplicationBundleDetailPDFView.as_view()
case_printout = CasePrintoutPDFView.as_view()
case_bundle_printout = CaseBundlePrintoutPDFView.as_view()
applicant_autocomplete = ApplicantAutocomplete.as_view()
