from django.shortcuts import render
from django.views.generic.base import View, TemplateView


class Home(TemplateView):

    template_name = "main_splash.html"

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        return context
