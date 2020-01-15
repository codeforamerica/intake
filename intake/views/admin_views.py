from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse

from project.services.query_params import get_url_for_ids
from intake import models, notifications, utils

import intake.services.submissions as SubmissionsService
import intake.services.applications_service as AppsService
import intake.services.bundles as BundlesService
import intake.services.tags as TagsService
import intake.services.pdf_service as PDFService
import intake.services.display_form_service as DisplayFormService

from intake.views.base_views import (
    ViewAppDetailsMixin, not_allowed, NoBrowserCacheOnGetMixin)
from intake.views.app_detail_views import ApplicationDetail


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
        apps = AppsService.filter_to_org_if_not_staff(
            submission.applications.all(), request.user)
        AppsService.handle_apps_opened(self, apps)
        response = HttpResponse(pdf.pdf, content_type='application/pdf')
        return response


def get_tabs_for_org_user(organization, active_tab):
    tabs = [
        {
            'url': reverse('intake-app_unread_index'),
            'label': 'Unread',
            'count': AppsService.get_unread_apps_per_org_count(organization),
            'is_active': False},
        {
            'url': reverse('intake-app_needs_update_index'),
            'label': 'Needs Status Update',
            'count': AppsService.get_needs_update_apps_per_org_count(
                organization),
            'is_active': False},
        {
            'url': reverse('intake-app_all_index'),
            'label': 'All',
            'count': AppsService.get_all_apps_per_org_count(organization),
            'is_active': False}
    ]

    active_tab_count = activate_tab_by_label(tabs, active_tab)

    return tabs, active_tab_count


def get_tabs_for_staff_user(active_tab):
    tabs = [
        {
            'url': reverse('intake-app_all_index'),
            'label': 'All Applications',
            'count': models.FormSubmission.objects.count(),
            'is_active': False},
        {
            'url': reverse('intake-app_cnl_index'),
            'label': 'County-Not-Listed',
            'count': models.FormSubmission.objects.filter(
                organizations__slug='cfa').count(),
            'is_active': False}
    ]

    active_tab_count = activate_tab_by_label(tabs, active_tab)

    return tabs, active_tab_count


def activate_tab_by_label(tabs, label):
    for tab in tabs:
        if tab['label'] == label:
            tab['is_active'] = True
            return tab['count']


class ApplicationIndex(ViewAppDetailsMixin, TemplateView):
    """A paginated list view of all the applications to a user's organization.
    """
    template_name = "app_index.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_staff = self.request.user.is_staff
        context['show_pdf'] = self.request.user.profile.should_see_pdf()
        context['body_class'] = 'admin'
        if is_staff:
            context['ALL_TAG_NAMES'] = TagsService.get_all_used_tag_names()
            context['results'] = \
                SubmissionsService.get_submissions_for_followups(
                    self.request.GET.get('page'))
            context['app_index_tabs'], count = get_tabs_for_staff_user(
                'All Applications')
            context['app_index_scope_title'] = 'Applications'
        else:
            context['results'] = \
                AppsService.get_all_applications_for_org_user(
                    self.request.user, self.request.GET.get('page'))
            context['app_index_tabs'], count = get_tabs_for_org_user(
                self.request.user.profile.organization, 'All')
            context['app_index_scope_title'] = "All Applications To {}".format(
                self.request.user.profile.organization.name)
        if count == 0:
            context['no_results'] = 'You have no applications.'
            context['csv_download_link'] = None
        else:
            context['csv_download_link'] = reverse('intake-csv_download')
        context['page_counter'] = \
            utils.get_page_navigation_counter(
                page=context['results'],
                wing_size=9)
        return context


class ApplicationUnreadIndex(NoBrowserCacheOnGetMixin, ApplicationIndex):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['results'] = AppsService.get_unread_applications_for_org_user(
                self.request.user, self.request.GET.get('page'))
        context['app_index_tabs'], count = get_tabs_for_org_user(
            self.request.user.profile.organization, 'Unread')
        context['app_index_scope_title'] = "{} Unread Applications".format(
            count)
        if count == 0:
            context['print_all_link'] = None
            context['no_results'] = "You have read all new applications!"
        else:
            context['print_all_link'] = get_url_for_ids(
                'intake-pdf_bundle_wrapper_view',
                AppsService.get_unread_applications_for_org(
                    self.request.user.profile.organization
                        ).values_list('id', flat=True)
                )
        context['csv_download_link'] = None
        return context

    def get(self, request):
        if request.user.is_staff:
            return redirect(reverse_lazy('intake-app_index'))
        else:
            return super().get(self, request)


class ApplicationNeedsUpdateIndex(ApplicationUnreadIndex):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['results'] = \
            AppsService.get_applications_needing_updates_for_org_user(
                self.request.user, self.request.GET.get('page'))
        context['app_index_tabs'], count = get_tabs_for_org_user(
            self.request.user.profile.organization,
            'Needs Status Update')
        if count == 0:
            context['no_results'] = "You have updated all applications!"
        else:
            context['no_results'] = None
        context['print_all_link'] = None
        context['csv_download_link'] = None
        context['app_index_scope_title'] = \
            "{} Applications Need Status Updates".format(count)
        return context


class ApplicationCountyNotListedIndex(ApplicationIndex):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return not_allowed(request)
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        is_staff = self.request.user.is_staff
        if is_staff:
            context['results'] = SubmissionsService.get_all_cnl_submissions(
                self.request.GET.get('page'))
            context['app_index_tabs'], count = get_tabs_for_staff_user(
                'County-Not-Listed')
        else:
            context['app_index_tabs'], count = get_tabs_for_org_user(
                self.request.user.profile.organization,
                'County-Not-Listed')
        if count == 0:
            context['no_results'] = "There are no CNL applications!"
        else:
            context['no_results'] = None
        context['print_all_link'] = None
        context['csv_download_link'] = None
        context['app_index_scope_title'] = \
            "{} County-Not-Listed Applications".format(count)
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
            DisplayFormService.get_display_form_for_user_and_submission(
                request.user, submission)
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
            DisplayFormService.get_display_form_for_user_and_submission(
                request.user, submission)
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
        BundlesService.mark_opened(bundle, request.user)
        filename, pdf_bytes = PDFService.get_concatenated_printout_for_bundle(
            request.user, bundle)
        response = HttpResponse(
            pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="{}"'.format(filename)
        return response


filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_unread_index = ApplicationUnreadIndex.as_view()
app_needs_update_index = ApplicationNeedsUpdateIndex.as_view()
app_bundle = ApplicationBundle.as_view()
app_bundle_detail = ApplicationBundleDetail.as_view()
app_bundle_detail_pdf = ApplicationBundleDetailPDFView.as_view()
case_bundle_printout = CaseBundlePrintoutPDFView.as_view()
app_cnl_index = ApplicationCountyNotListedIndex.as_view()
