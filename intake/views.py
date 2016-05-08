from django.conf import settings
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy

from django.http import HttpResponseNotFound
from django.views.generic import View
from django.views.generic.base import TemplateView



from django.core import mail

from intake.models import FormSubmission
from intake.notifications import new_submission_email



class Home(TemplateView):
    template_name = "main_splash.html"


class Apply(View):

    def get(self, request):
        return render(request, "application_form.html")

    def post(self, request):
        submission = FormSubmission(answers=dict(request.POST))
        submission.save()
        new_submission_email.send(submission=submission, request=request)
        return redirect(reverse_lazy('intake-thanks'))


class Thanks(TemplateView):
    template_name = "thanks.html"


class FilledPDF(View):

    def get(self, request, submission_id):
        # render the pdf
        # send the notification
        # return the filled pdf
        return "hello"


