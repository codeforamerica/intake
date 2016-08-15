from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView



from django.core import mail

from intake import models, notifications, constants
from formation.forms import county_form_selector, SelectCountyForm
from project.jinja2 import url_with_ids



class Home(TemplateView):
    template_name = "main_splash.jinja"


class MultiStepFormViewBase(FormView):
    session_storage_key = "form_in_progress"

    def update_session_data(self):
        form_data = self.request.session.get(self.session_storage_key, {})
        post_data = dict(self.request.POST.lists())
        form_data.update(post_data)
        self.request.session[self.session_storage_key] = form_data
        return form_data

    def get_session_data(self):
        data = self.request.session.get(self.session_storage_key, {})
        return MultiValueDict(data)

    def put_errors_in_flash_messages(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, self.error_message)
        self.put_errors_in_flash_messages(form)
        return super().form_invalid(form, *args, **kwargs)


class MultiStepApplicationView(MultiStepFormViewBase):
    template_name = "forms/county_form.jinja"
    success_url = reverse_lazy('intake-thanks')
    error_message = _("There were some problems with your application. Please check the errors below.")

    def confirmation(self, submission):
        flash_messages = submission.send_confirmation_notifications()
        for message in flash_messages:
            messages.success(self.request, message)

    def save_submission_and_send_notifications(self, form):
        submission = models.FormSubmission(answers=form.cleaned_data)
        submission.save()
        submission.counties = self.get_counties()
        number = models.FormSubmission.objects.count()
        notifications.slack_new_submission.send(
            submission=submission, request=self.request, submission_count=number)
        self.confirmation(submission)

    def form_valid(self, form):
        self.save_submission_and_send_notifications(form)
        return super().form_valid(form)


class MultiCountyApplicationView(MultiStepApplicationView):

    def get_counties(self):
        session_data = self.get_session_data()
        county_slugs = session_data.getlist('counties')
        return models.County.objects.filter(slug__in=county_slugs)

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
    '''Intended to provide a final acceptance of a form,
    after any necessary warnings have been raised.
    It follows the `Apply` view, which checks for warnings.
    '''
    incoming_message = _("Please double check the form. Some parts are empty and may cause delays.")

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
    '''The initial application page.
    Checks for warnings, and if they exist, redirects to a confirmation page.
    '''
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


class Thanks(TemplateView):
    template_name = "thanks.jinja"


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

    def get_pdf_for_user(self, request, submission_data):
        organization = request.user.profile.organization
        fillable = models.FillablePDF.objects.filter(organization=organization).first()
        if isinstance(submission_data, list):
            return fillable.fill_many(submission_data)
        return fillable.fill(submission_data)

    def get(self, request, submission_id):
        submissions = list(models.FormSubmission.get_permitted_submissions(
            request.user, [submission_id]))
        if not submissions:
            return self.not_allowed(request)
        submission = submissions[0]
        pdf = self.get_pdf_for_user(request, submission)
        self.mark_viewed(request, submission)
        return HttpResponse(pdf,
            content_type="application/pdf")


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
        context['stats'] = {
            'received': models.FormSubmission.objects.count(),
            'opened': models.FormSubmission.get_opened_apps().count()
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
            show_pdf=request.user.profile.should_see_pdf(),
            app_ids=[sub.id for sub in submissions]
            )
        self.mark_viewed(request, submissions)
        return render(request, "app_bundle.jinja", context)


class FilledPDFBundle(FilledPDF, MultiSubmissionMixin):
    def get(self, request):
        submissions = self.get_submissions_from_params(request)
        if not submissions:
            return self.not_allowed(request)
        pdf = self.get_pdf_for_user(request, list(submissions))
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


######## REDIRECT VIEWS ########
# for backwards compatibility

class PermanentRedirectView(View):
    '''Permanently redirects to a url
    by default, it will build a url from any kwargs
    self.build_redirect_url() can be overridden to provide logic
    '''
    redirect_view_name = None

    def build_redirect_url(self, request, **kwargs):
        return reverse_lazy(
            self.redirect_view_name,
            kwargs=dict(**kwargs))

    def get(self, request, **kwargs):
        redirect_url = self.build_redirect_url(request, **kwargs)
        return redirect(redirect_url, permanent=True)


class SingleIdPermanentRedirect(PermanentRedirectView):
    '''Redirects from 
        sanfrancisco/0efd75e8721c4308a8f3247a8c63305d/
    to
        application/3/
    '''
    def build_redirect_url(self, request, submission_id):
        submission = models.FormSubmission.objects.get(old_uuid=submission_id)
        return reverse_lazy(self.redirect_view_name,
            kwargs=dict(submission_id=submission.id)
            )


class MultiIdPermanentRedirect(PermanentRedirectView):
    '''Redirects from
        sanfrancisco/bundle/?keys=0efd75e8721c4308a8f3247a8c63305d|b873c4ceb1cd4939b1d4c890997ef29c
    to
        applications/bundle/?ids=3,4
    '''
    def build_redirect_url(self, request):
        key_set = request.GET.get('keys')
        uuids = [key for key in key_set.split('|')]
        submissions = models.FormSubmission.objects.filter(
            old_uuid__in=uuids)
        return url_with_ids(
            self.redirect_view_name,
            [s.id for s in submissions])








