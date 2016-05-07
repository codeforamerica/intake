from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy

from django.http import HttpResponseNotFound
from django.views.generic import View
from django.views.generic.base import TemplateView

from intake.models import FormSubmission


class Home(TemplateView):
    template_name = "main_splash.html"


class Apply(View):

    def get(self, request):
        return render(request, "application_form.html")

    def post(self, request):
        submission = FormSubmission(answers=dict(request.POST))
        submission.save()
        return redirect(reverse_lazy('intake-thanks'))


class Thanks(TemplateView):
    template_name = "thanks.html"


class PDFView(View):

    def get(self, request):
        pass