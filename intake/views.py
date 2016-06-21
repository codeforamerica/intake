from django.conf import settings
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView



from django.core import mail

from intake import models, notifications
from project.jinja2 import url_with_ids



class Home(TemplateView):
    template_name = "main_splash.jinja"


class Apply(View):

    def get(self, request):
        return render(request, "application_form.jinja")

    def post(self, request):
        submission = models.FormSubmission.create_from_answers(dict(request.POST))
        number = models.FormSubmission.objects.count()
        notifications.slack_new_submission.send(
            submission=submission, request=request, submission_count=number)
        return redirect(reverse_lazy('intake-thanks'))


class Thanks(TemplateView):
    template_name = "thanks.jinja"


class PrivacyPolicy(TemplateView):
    template_name = "privacy_policy.jinja"


class FilledPDF(View):

    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        fillable = models.FillablePDF.get_default_instance()
        pdf = fillable.fill(submission)
        # wrapper = FileWrapper(file(filename))
        # response = HttpResponse(wrapper, content_type='text/plain')
        # response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filename)
        # response['Content-Length'] = os.path.getsize(filename)
        # return response
        models.FormSubmission.mark_viewed([submission], request.user)
        return HttpResponse(pdf,
            content_type="application/pdf")


class ApplicationIndex(TemplateView):
    template_name = "app_index.jinja"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = models.FormSubmission.objects.all().prefetch_related('logs__user')
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

    def get_ids_from_params(self, request):
        id_set = request.GET.get('ids')
        return [int(i) for i in id_set.split(',')]


class ApplicationBundle(View, MultiSubmissionMixin):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = list(models.FormSubmission.objects.filter(
            pk__in=submission_ids))
        models.FormSubmission.mark_viewed(submissions, request.user)
        return render(
            request,
            "app_bundle.jinja", {
                'submissions': submissions,
                'count': len(submissions),
                'app_ids': submission_ids
             })


class FilledPDFBundle(View, MultiSubmissionMixin):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = models.FormSubmission.objects.filter(
            pk__in=submission_ids)
        fillable = models.FillablePDF.get_default_instance()
        pdf = fillable.fill_many(submissions)
        return HttpResponse(pdf,
            content_type="application/pdf")


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
            event_type=models.ApplicationLogEntry.DELETED
            )
        submission.delete()
        notifications.slack_submissions_deleted.send(
            submissions=[submission],
            user=request.user)
        return redirect(reverse_lazy('intake-app_index'))


class MarkSubmissionStepView(View, MultiSubmissionMixin):

    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        next_param = request.GET.get('next',
            reverse_lazy('intake-app_index'))
        models.ApplicationLogEntry.log_multiple(
            self.process_step, submission_ids, request.user)
        submissions = models.FormSubmission.objects.filter(pk__in=submission_ids)
        if hasattr(self, 'notification_function'):
            self.notification_function(
                submissions=list(submissions), user=request.user)
        return redirect(next_param)


class MarkProcessed(MarkSubmissionStepView):
    process_step = models.ApplicationLogEntry.PROCESSED
    notification_function = notifications.slack_submissions_processed.send


home = Home.as_view()
apply_form = Apply.as_view()
thanks = Thanks.as_view()
privacy = PrivacyPolicy.as_view()
stats = Stats.as_view()
filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
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








