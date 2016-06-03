from django.conf import settings
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView



from django.core import mail

from intake import models, notifications



class Home(TemplateView):
    template_name = "main_splash.html"


class Apply(View):

    def get(self, request):
        return render(request, "application_form.html")

    def post(self, request):
        submission = models.FormSubmission(answers=dict(request.POST))
        submission.save()
        notifications.slack_new_submission.send(
            submission=submission, request=request)
        return redirect(reverse_lazy('intake-thanks'))


class Thanks(TemplateView):
    template_name = "thanks.html"


class FilledPDF(View):

    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        fillable = models.FillablePDF.objects.get(id=1)
        pdf = fillable.fill(submission.answers)
        # wrapper = FileWrapper(file(filename))
        # response = HttpResponse(wrapper, content_type='text/plain')
        # response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filename)
        # response['Content-Length'] = os.path.getsize(filename)
        # return response
        notifications.slack_submission_viewed.send(
            submission=submission, user=request.user)
        return HttpResponse(pdf,
            content_type="application/pdf")


class ApplicationIndex(TemplateView):
    template_name = "app_index.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = models.FormSubmission.objects.all()
        context['body_class'] = 'admin'
        return context


class ApplicationBundle(View):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = list(models.FormSubmission.objects.filter(
            pk__in=submission_ids))
        notifications.slack_bundle_viewed.send(
            submissions=submissions, user=request.user)
        return render(
            request,
            "app_bundle.html", {
                'submissions': submissions,
                'count': len(submissions),
                'app_ids': submission_ids,
                'body_class': 'admin',
             })

    def get_ids_from_params(self, request):
        id_set = request.GET.get('ids')
        return [int(i) for i in id_set.split(',')]


class FilledPDFBundle(ApplicationBundle):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = models.FormSubmission.objects.filter(
            pk__in=submission_ids)
        fillable = models.FillablePDF.objects.get(id=1)
        pdf = fillable.fill_many([s.answers for s in submissions])
        return HttpResponse(pdf,
            content_type="application/pdf")


class Delete(View):
    template_name = "delete_page.html"
    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        return render(
            request,
            self.template_name, {
                'submission': submission,
                'body_class': 'admin',
                })

    def post(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        notifications.slack_submission_deleted.send(
            submission=submission,
            user=request.user)
        submission.delete()
        # add a message saying it's been deleted
        return redirect(reverse_lazy('intake-app_index'))



home = Home.as_view()
apply_form = Apply.as_view()
thanks = Thanks.as_view()
filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
delete_page = Delete.as_view()





