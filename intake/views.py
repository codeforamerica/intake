"""
Here are the important views in a rough order that follows the path of a
submission:

* `Home` - where a user would learn about the service and hit 'apply'
* `SelectCounty` - a user selects the counties they need help with. This stores
    the county selection in the session.
* `CountyApplication` - a dynamic form built based on the county selection data
    that was stored in the session. This view does most of the validation work.
* `Confirm` (maybe) - if warnings exist on the form, users will be directed
    here to confirm their submission. Unlike errors, warnings do not prevent
    submission. This is just a slightly reduced version of `CountyApplication`.
* `Thanks` - a confirmation page that shows data from the newly saved
    submission.

A daily notification is sent to organizations with a link to a bundle of their
new applications.

* `ApplicationBundle` - This is typically the main page that organization users
    will access. Here they will see a collection of new applications, and, if
    needed, can see a filled pdf for their intake forms. If they need a pdf
    it will be served in an iframe by `FilledPDFBundle`
* `ApplicationIndex` - This is a list page that lets an org user see all the
    applications to their organization, organized in a table. Here they can
    access links to `ApplicationDetail` and `FilledPDF` for each app.
* `ApplicationDetail` - This shows the detail of one particular FormSubmission
"""
import logging

from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView


from intake import models, notifications, constants
from user_accounts.models import Organization
from user_accounts.forms import OrganizationDetailsDisplayForm


logger = logging.getLogger(__name__)


class NoCountyCookiesError(Exception):
    pass


NOT_ALLOWED_MESSAGE = str(
    "Sorry, you are not allowed to access that client information. "
    "If you have any questions, please contact us at "
    "clearmyrecord@codeforamerica.org")

GENERIC_USER_ERROR_MESSAGE = _(
    "Oops! Something went wrong. This is embarrassing. If you noticed anything"
    " unusual, please email us: clearmyrecord@codeforamerica.org")


def not_allowed(request):
    messages.error(request, NOT_ALLOWED_MESSAGE)
    return redirect('intake-app_index')


class Home(TemplateView):
    """Homepage view which shows information about the service
    """
    template_name = "main_splash.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if constants.SCOPE_TO_LIVE_COUNTIES:
            counties = models.County.objects.prefetch_related(
                'organizations').filter(slug__in=[
                    constants.Counties.SAN_FRANCISCO,
                    constants.Counties.CONTRA_COSTA])
        else:
            counties = models.County.objects.prefetch_related(
                'organizations').all()
        context['counties'] = counties
        return context


class PrivacyPolicy(TemplateView):
    template_name = "privacy_policy.jinja"


class PartnerListView(TemplateView):
    template_name = "partner_list.jinja"

    def get_context_data(self, *args, **kwargs):
        return dict(
            counties=models.County.objects.prefetch_related(
                'organizations').all())


class PartnerDetailView(TemplateView):
    template_name = "partner_detail.jinja"

    def get(self, request, organization_slug):
        self.organization_slug = organization_slug
        return super().get(request)

    def get_context_data(self, *args, **kwargs):
        query = Organization.objects.prefetch_related(
            'addresses'
            ).filter(
            is_receiving_agency=True
            )
        organization = get_object_or_404(
                query, slug=self.organization_slug)
        return dict(
            organization=organization,
            display_form=OrganizationDetailsDisplayForm(organization))


class ApplicationDetail(View):
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
        submissions = list(models.FormSubmission.get_permitted_submissions(
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
        response = render(request, self.template_name, context)
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


class ApplicationIndex(TemplateView):
    """A list view of all the application to a user's organization.
    """
    template_name = "app_index.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = list(
            models.FormSubmission.get_permitted_submissions(
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
        return list(models.FormSubmission.get_permitted_submissions(
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
        bundle = models.ApplicationBundle\
            .get_or_create_for_submissions_and_user(submissions, request.user)
        forms = [
            submission.get_display_form_for_user(request.user)
            for submission in submissions]
        context = dict(
            forms=forms,
            count=len(submissions),
            show_pdf=request.user.profile.should_see_pdf(),
            app_ids=[sub.id for sub in submissions]
        )
        models.ApplicationLogEntry.log_bundle_opened(bundle, request.user)
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=request.user,
            bundle_url=bundle.get_external_url())
        return render(request, "app_bundle.jinja", context)


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
            forms=forms,
            count=len(submissions),
            show_pdf=bool(bundle.bundled_pdf),
            app_ids=[sub.id for sub in submissions],
            bundled_pdf_url=bundle.get_pdf_bundle_url())
        models.ApplicationLogEntry.log_bundle_opened(bundle, request.user)
        notifications.slack_submissions_viewed.send(
            submissions=submissions, user=request.user,
            bundle_url=bundle.get_external_url())
        return render(request, "app_bundle.jinja", context)


class ApplicationBundleDetailPDFView(View):
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
        bundle = models.ApplicationBundle\
            .get_or_create_for_submissions_and_user(submissions, request.user)
        return redirect(bundle.get_pdf_bundle_url())


class Delete(View):
    """A page to confirm the deletion of an individual application.
    """
    template_name = "delete_page.jinja"

    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        return render(
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


class MarkSubmissionStepView(View, MultiSubmissionMixin):

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


home = Home.as_view()
partner_list = PartnerListView.as_view()
partner_detail = PartnerDetailView.as_view()
privacy = PrivacyPolicy.as_view()
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
