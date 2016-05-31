from django.conf import settings
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView



from django.core import mail

from intake import models
from intake.notifications import new_submission_email



class Home(TemplateView):
    template_name = "main_splash.html"


class Apply(View):

    def get(self, request):
        return render(request, "application_form.html")

    def post(self, request):
        submission = models.FormSubmission(answers=dict(request.POST))
        submission.save()
        new_submission_email.send(submission=submission, request=request)
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
        return HttpResponse(pdf,
            content_type="application/pdf")

class ApplicationIndex(TemplateView):

    template_name = "app_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = models.FormSubmission.objects.all()
        return context

