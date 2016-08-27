from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView


from django.core import mail

from intake import models, notifications, constants
from formation.forms import county_form_selector, SelectCountyForm
from project.jinja2 import url_with_ids, oxford_comma


class Home(TemplateView):
    """Homepage view which lists available counties.
    """

    template_name = "main_splash.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        counties = models.County.objects.prefetch_related(
            'organizations').all()
        context['counties'] = counties
        return context


class GetFormSessionDataMixin:
    """Responsable for storing form data in a session.
    """

    session_storage_key = "form_in_progress"

    def get_session_data(self):
        data = self.request.session.get(self.session_storage_key, {})
        return MultiValueDict(data)

    def get_counties(self):
        session_data = self.get_session_data()
        county_slugs = session_data.getlist('counties')
        return models.County.objects.filter(slug__in=county_slugs)

    def get_county_context(self):
        counties = self.get_counties()
        return dict(
            counties=counties,
            county_list=[county.name + " County" for county in counties]
        )


class MultiStepFormViewBase(GetFormSessionDataMixin, FormView):
    """Makes a form that goes across multiple pages.
    """

    ERROR_MESSAGE = _((
        "There were some problems with your application."
        " Please check the errors below."
    ))

    def update_session_data(self):
        form_data = self.request.session.get(self.session_storage_key, {})
        post_data = dict(self.request.POST.lists())
        form_data.update(post_data)
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


class MultiStepApplicationView(MultiStepFormViewBase):
    """Manages multiple page forms and their confirmation and submission.
    """

    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')

    def confirmation(self, submission):
        county_list = [
            name + " County" for name in submission.get_nice_counties()]
        msg = _("You have applied for help in ") + oxford_comma(county_list)
        messages.success(self.request, msg)
        flash_messages = submission.send_confirmation_notifications()
        for message in flash_messages:
            messages.success(self.request, message)

    def save_submission_and_send_notifications(self, form):
        submission = models.FormSubmission(answers=form.cleaned_data)
        submission.save()
        submission.counties = self.get_counties()
        number = models.FormSubmission.objects.count()
        notifications.slack_new_submission.send(
            submission=submission, request=self.request,
            submission_count=number)
        counties = submission.counties.values_list('pk', flat=True)
        fillable_pdfs = models.FillablePDF.objects.filter(
            organization__county__in=counties).all()

        for fillable_pdf in fillable_pdfs:
            filled_pdf_bytes = fillable_pdf.fill(submission)
            pdf_file = SimpleUploadedFile('filled.pdf', filled_pdf_bytes,
                                          content_type='application/pdf')
            pdf = models.FilledPDF(
                pdf=pdf_file,
                original_pdf=fillable_pdf,
                submission=submission,
            )
            pdf.save()
        self.confirmation(submission)

    def form_valid(self, form):
        self.save_submission_and_send_notifications(form)
        return super().form_valid(form)


class MultiCountyApplicationView(MultiStepApplicationView):
    """Extends `MultiStepApplicationView` with county information."""

    def get_form_kwargs(self):
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST})
        return kwargs

    def get_form_class(self):
        session_data = self.get_session_data()
        counties = session_data.getlist('counties')
        return county_form_selector.get_combined_form_class(counties=counties)


class Confirm(MultiCountyApplicationView):
    """Intended to provide a final acceptance of a form,
    after any necessary warnings have been raised.
    It follows the `Apply` view, which checks for warnings.
    """
    incoming_message = _(
        "Please double check the form. Some parts are empty and may cause delays.")

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


class CountyApplication(MultiCountyApplicationView):
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


class SelectCounty(MultiStepFormViewBase):
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def form_valid(self, form):
        form_data = self.update_session_data()
        return super().form_valid(form)


class Thanks(TemplateView, GetFormSessionDataMixin):
    template_name = "thanks.jinja"

    def get_context_data(self, *args, **kwargs):
        context = self.get_county_context()
        context['intake_constants'] = constants
        return context


class PrivacyPolicy(TemplateView):
    template_name = "privacy_policy.jinja"


class ApplicationDetail(View):
    template_name = "app_detail.jinja"
    not_allowed_message = str(
        "Sorry, you are not allowed to access that client information. "
        "If you have any questions, please contact us at "
        "clearmyrecord@codeforamerica.org")

    def not_allowed(self, request):
        messages.error(request, self.not_allowed_message)
        return redirect('intake-app_index')

    def mark_viewed(self, request, submissions):
        if not isinstance(submissions, list):
            submissions = [submissions]
        models.FormSubmission.mark_viewed(submissions, request.user)

    def get(self, request, submission_id):
        if request.user.profile.should_see_pdf():
            return redirect(reverse_lazy('intake-filled_pdf',
                                         kwargs=dict(submission_id=submission_id)))
        submissions = list(models.FormSubmission.get_permitted_submissions(
            request.user, [submission_id]))
        if not submissions:
            return self.not_allowed(request)
        submission = submissions[0]
        context = dict(submission=submission)
        self.mark_viewed(request, submission)
        return render(request, self.template_name, context)


class FilledPDF(ApplicationDetail):

    def get(self, request, submission_id):
        submissions = list(models.FormSubmission.get_permitted_submissions(
            request.user, [submission_id]))
        if not submissions:
            return self.not_allowed(request)
        submission = submissions[0]
        pdf = submission.filledpdf_set.first()
        self.mark_viewed(request, submission)
        response = HttpResponse(pdf.pdf,
                                content_type='application/pdf')
        response['Content-Disposition'] = \
            'attachment; filename=submission%s.pdf' % submission_id
        return response


class ApplicationIndex(TemplateView):
    template_name = "app_index.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = list(models.FormSubmission.get_permitted_submissions(
            self.request.user, related_objects=True))
        context['body_class'] = 'admin'
        return context


class Stats(TemplateView):
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        county_totals = []
        counties = models.County.objects.all()
        for county in counties:
            county_totals.append(dict(
                count=models.FormSubmission.objects.filter(
                    counties=county).count(),
                county_name=county.name))
        context['stats'] = {
            'total_all_counties': models.FormSubmission.objects.count(),
            'county_totals': county_totals
        }
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

    def get(self, request):
        submissions = self.get_submissions_from_params(request)
        if not submissions:
            return self.not_allowed(request)
        context = dict(
            submissions=submissions,
            count=len(submissions),
            show_pdf=request.user.profile.should_see_pdf(),
            app_ids=[sub.id for sub in submissions]
        )
        self.mark_viewed(request, submissions)
        return render(request, "app_bundle.jinja", context)


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

    def get(self, request):
        submissions = self.get_submissions_from_params(request)
        if not submissions:
            return self.not_allowed(request)
        # TODO: get from FilledPDFs and update cronjob
        pdf = get_pdf_for_user(request.user, list(submissions))
        return HttpResponse(pdf, content_type="application/pdf")


class Delete(View):
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

    def get_organization(self, user):
        """Get the organization for logging this step.
        """
        return user.profile.organization

    def get(self, request):
        submissions = self.get_submissions_from_params(request)
        submission_ids = [sub.id for sub in submissions]
        next_param = request.GET.get('next',
                                     reverse_lazy('intake-app_index'))
        models.ApplicationLogEntry.log_multiple(
            self.process_step, submission_ids, request.user,
            organization=self.get_organization(request.user))
        if hasattr(self, 'notification_function'):
            self.notification_function(
                submissions=submissions, user=request.user)
        return redirect(next_param)


class MarkProcessed(MarkSubmissionStepView):
    process_step = models.ApplicationLogEntry.PROCESSED
    notification_function = notifications.slack_submissions_processed.send


home = Home.as_view()
county_application = CountyApplication.as_view()
select_county = SelectCounty.as_view()
confirm = Confirm.as_view()
thanks = Thanks.as_view()
privacy = PrivacyPolicy.as_view()
stats = Stats.as_view()
filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
app_detail = ApplicationDetail.as_view()
mark_processed = MarkProcessed.as_view()
delete_page = Delete.as_view()


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
