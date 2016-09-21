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
import csv
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages

from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from intake import models, notifications, constants
from user_accounts.models import Organization
from formation.forms import (
    county_form_selector, DeclarationLetterFormSpec, SelectCountyForm)
from project.jinja2 import url_with_ids, oxford_comma


logger = logging.getLogger(__name__)

NOT_ALLOWED_MESSAGE = str(
    "Sorry, you are not allowed to access that client information. "
    "If you have any questions, please contact us at "
    "clearmyrecord@codeforamerica.org")


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


class GetFormSessionDataMixin:
    """Responsible for retreiving form data stored in a session.

    This adds methods for getting session data, but not for setting it
    """
    session_storage_key = "form_in_progress"

    def get_session_data(self):
        data = self.request.session.get(self.session_storage_key, {})
        return MultiValueDict(data)

    def get_counties(self):
        session_data = self.get_session_data()
        county_slugs = session_data.getlist('counties')
        return models.County.objects.filter(slug__in=county_slugs).all()

    def get_organizations(self):
        session_data = self.get_session_data()
        org_slugs = session_data.getlist('organizations')
        return Organization.objects.filter(slug__in=org_slugs)

    def get_county_context(self):
        counties = self.get_counties()
        return dict(
            counties=counties,
            county_list=[county.name + " County" for county in counties]
        )

    def get_applicant_id(self):
        return self.request.session.get('applicant_id')


class MultiStepFormViewBase(GetFormSessionDataMixin, FormView):
    """A FormView saves form data in a session for persistence between URLs.
    """
    ERROR_MESSAGE = _(str(
        "There were some problems with your application. "
        "Please check the errors below."))

    def update_session_data(self, **extra_data):
        form_data = self.request.session.get(self.session_storage_key, {})
        post_data = dict(self.request.POST.lists())
        form_data.update(post_data)
        if extra_data:
            form_data.update(extra_data)
        self.request.session[self.session_storage_key] = form_data
        return form_data

    def put_errors_in_flash_messages(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, self.ERROR_MESSAGE)
        self.put_errors_in_flash_messages(form)
        return super().form_invalid(form, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(self.get_county_context())
        return context

    def create_applicant(self):
        applicant = models.Applicant()
        applicant.save()
        self.request.session['applicant_id'] = applicant.id
        return applicant

    def log_application_event(self, name, **data):
        applicant_id = self.get_applicant_id()
        event = models.ApplicationEvent(
            name=name,
            applicant_id=applicant_id,
            data=data or {}
        )
        event.save()
        return event


class MultiCountyApplicationBase(MultiStepFormViewBase):
    """A multi-page dynamic form view based on data stored in the session.

    The form class is created dynamically based on data stored in the session.
    Once created, the form class is fed POST data from the session.
    """
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')

    def get_form_kwargs(self):
        """Ensures that the dynamic form class is instantiated with POST data.
        """
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST})
        return kwargs

    def get_form_specs(self):
        session_data = self.get_session_data()
        counties = session_data.getlist('counties')
        return county_form_selector.get_combined_form_spec(counties=counties)

    def get_form_class(self):
        """Builds a form class dynamically, based on a list of county slugs
        stored in the session.
        """
        spec = self.get_form_specs()
        return spec.build_form_class()

    def create_confirmations_for_user(self, submission):
        """Sends texts/emails to user and adds flash messages
        """
        county_list = [
            name + " County" for name in submission.get_nice_counties()]
        joined_county_list = oxford_comma(county_list)
        full_message = _("You have applied for help in ") + joined_county_list
        messages.success(self.request, full_message)
        # send emails and texts
        sent_confirmations = submission.send_confirmation_notifications()
        for message in sent_confirmations:
            messages.success(self.request, message)

    def get_orgs_for_answers(self, answers):
        counties = self.get_counties()
        return [
            county.get_receiving_agency(answers)
            for county in counties]

    def save_submission(self, form, organizations):
        """Save the submission data
        """
        applicant_id = self.get_applicant_id()
        submission = models.FormSubmission(
            answers=form.cleaned_data,
            applicant_id=applicant_id)
        submission.save()
        submission.organizations.add(*organizations)
        self.log_application_event(
            constants.ApplicationEventTypes.APPLICATION_SUBMITTED)
        # TODO: check for cerrect org in view tests
        return submission

    def send_notifications(self, submission):
        number = models.FormSubmission.objects.count()
        # TODO: say which orgs this is going to in notification
        notifications.slack_new_submission.send(
            submission=submission, request=self.request,
            submission_count=number)
        self.create_confirmations_for_user(submission)

    def save_submission_and_send_notifications(self, form):
        organizations = self.get_orgs_for_answers(form.cleaned_data)
        submission = self.save_submission(form, organizations)
        self.send_notifications(submission)

    def form_valid(self, form):
        # if for alameda, send to declaration letter
        organizations = self.get_orgs_for_answers(form.cleaned_data)
        self.update_session_data(
            organizations=[org.slug for org in organizations])
        if any([org.requires_declaration_letter for org in organizations]):
            return redirect(reverse('intake-write_letter'))
        submission = self.save_submission(form, organizations)
        self.send_notifications(submission)
        submission.fill_pdfs()
        if any([org.requires_rap_sheet for org in organizations]):
            return redirect(reverse('intake-rap_sheet'))
        return super().form_valid(form)


class Confirm(MultiCountyApplicationBase):
    """Intended to provide a final acceptance of a form,
    after any necessary warnings have been raised.
    It follows the `Apply` view, which checks for warnings.
    """
    incoming_message = _(str(
        "Please double check the form. "
        "Some parts are empty and may cause delays."))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        form_data = self.get_session_data()
        if form_data:
            form = self.get_form_class()(data=form_data)
            # make sure the form has warnings.
            # trigger data cleaning
            form.is_valid()
            if form.warnings:
                messages.warning(self.request, self.incoming_message)
            context['form'] = form
        return context


class CountyApplication(MultiCountyApplicationBase):
    """The initial application page.
    Checks for warnings, and if they exist, redirects to a confirmation page.
    """
    confirmation_url = reverse_lazy('intake-confirm')

    def form_valid(self, form):
        """If no errors, check for warnings, redirect to confirmation if needed
        """
        if form.warnings:
            # save the post data and move them to confirmation step
            self.update_session_data()
            return redirect(self.confirmation_url)
        else:
            return super().form_valid(form)


class DeclarationLetterView(MultiCountyApplicationBase):
    template_name = "forms/declaration_letter_form.jinja"

    form_spec = DeclarationLetterFormSpec()

    def get(self, request):
        # TODO: refactor to not check form validity twice, don't grab the
        # session data too many times
        data = self.get_session_data()
        if not data:
            logger.warn(
                "{} hit with no existing session data".format(
                    self.__class__.__name__))
            return redirect(reverse('intake-apply'))
        return super().get(request)

    def get_form_class(self):
        return self.form_spec.build_form_class()

    def form_valid(self, declaration_letter_form):
        BaseCountyFormSpec = super().get_form_specs()
        Form = (
            self.form_spec | BaseCountyFormSpec
        ).build_form_class()
        data = self.get_session_data()
        data.update(declaration_letter_form.cleaned_data)
        form = Form(data)
        form.is_valid()
        self.save_submission_and_send_notifications(form)
        return MultiStepFormViewBase.form_valid(self, form)


class DeclarationLetterReviewPage(DeclarationLetterView):
    template_name = "forms/declaration_letter_review.jinja"
    # display_form_spec = DeclarationLetterFormDisplaySpec()

    def get(self, request):
        # get the session data
        # put it in the display form spec
        # render the template with the instantiated display form
        return super().get(request)

    def post(self, request):
        # skip form validity checks
        # this is a read only form
        # if  'edit_letter'
            # return redirect to DeclarationLetterView
        # if  'finish_letter'
            # save submission and redirect to thanks
        return super().post(request)


class SelectCounty(MultiStepFormViewBase):
    """A page where users select the counties they'd like help with.

    The user's county selection is stored in the session.
    """
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def form_valid(self, form):
        self.update_session_data()
        self.create_applicant()
        self.log_application_event(
            constants.ApplicationEventTypes.APPLICATION_STARTED,
            referrer=self.request.session.get('referrer'),
            ip=self.request.ip_address,
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
        )
        return super().form_valid(form)


class Thanks(TemplateView, GetFormSessionDataMixin):
    """A confirmation page that shows flash messages and next steps for a
    user.
    """
    template_name = "thanks.jinja"

    def get_context_data(self, *args, **kwargs):
        context = self.get_county_context()
        context['intake_constants'] = constants
        return context


class RAPSheetInstructions(TemplateView, GetFormSessionDataMixin):
    template_name = "rap_sheet_instructions.jinja"

    def get_context_data(self, *args, **kwargs):
        context = {}
        applicant_id = self.get_applicant_id()
        if applicant_id:
            organizations = Organization.objects.filter(
                submissions__applicant_id=applicant_id)
            context['organizations'] = organizations
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
        query = Organization.objects.filter(
            is_receiving_agency=True
            ).prefetch_related('county')
        return dict(
            organization=get_object_or_404(
                query, slug=self.organization_slug))


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
        context = dict(submission=submission)
        self.mark_viewed(request, submission)
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


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        county_totals = []
        counties = models.County.objects.all()
        for county in counties:
            county_totals.append(dict(
                count=models.FormSubmission.objects.filter(
                    organizations__county=county).count(),
                county_name=county.name))
        context['stats'] = {
            'total_all_counties': models.FormSubmission.objects.count(),
            'county_totals': county_totals
        }
        return context


class DailyTotals(View):

    def get(self, request):
        totals = list(models.FormSubmission.get_daily_totals())
        response = HttpResponse(content_type='text/csv')
        filename = 'daily_totals.csv'
        content_disposition = 'attachment; filename="{}"'.format(filename)
        response['Content-Disposition'] = content_disposition
        keys = [
            "Day", "All",
            constants.CountyNames.SAN_FRANCISCO,
            constants.CountyNames.CONTRA_COSTA,
            constants.CountyNames.ALAMEDA,
        ]
        writer = csv.DictWriter(
            response,
            fieldnames=keys,
            quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for item in totals:
            writer.writerow(item)
        return response


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
        context = dict(
            submissions=submissions,
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
        context = dict(
            submissions=submissions,
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
select_county = SelectCounty.as_view()
county_application = CountyApplication.as_view()
confirm = Confirm.as_view()
write_letter = DeclarationLetterView.as_view()
review_letter = DeclarationLetterReviewPage.as_view()
thanks = Thanks.as_view()
rap_sheet_info = RAPSheetInstructions.as_view()
partner_list = PartnerListView.as_view()
partner_detail = PartnerDetailView.as_view()
privacy = PrivacyPolicy.as_view()
stats = Stats.as_view()
daily_totals = DailyTotals.as_view()
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

# REDIRECT VIEWS for backwards compatibility


class PermanentRedirectView(View):
    """Permanently redirects to a url
    by default, it will build a url from any kwargs
    self.build_redirect_url() can be overridden to provide logic
    """
    redirect_view_name = None

    def build_redirect_url(self, request, **kwargs):
        return reverse_lazy(
            self.redirect_view_name,
            kwargs=dict(**kwargs))

    def get(self, request, **kwargs):
        redirect_url = self.build_redirect_url(request, **kwargs)
        return redirect(redirect_url, permanent=True)


class SingleIdPermanentRedirect(PermanentRedirectView):
    """Redirects from
        sanfrancisco/0efd75e8721c4308a8f3247a8c63305d/
    to
        application/3/
    """

    def build_redirect_url(self, request, submission_id):
        submission = models.FormSubmission.objects.get(old_uuid=submission_id)
        return reverse_lazy(self.redirect_view_name,
                            kwargs=dict(submission_id=submission.id)
                            )


class MultiIdPermanentRedirect(PermanentRedirectView):
    """Redirects from
        sanfrancisco/bundle/?keys=0efd75e8721c4308a8f3247a8c63305d|b873c4ceb1cd4939b1d4c890997ef29c
    to
        applications/bundle/?ids=3,4
    """

    def build_redirect_url(self, request):
        key_set = request.GET.get('keys')
        uuids = [key for key in key_set.split('|')]
        submissions = models.FormSubmission.objects.filter(
            old_uuid__in=uuids)
        return url_with_ids(
            self.redirect_view_name,
            [s.id for s in submissions])
