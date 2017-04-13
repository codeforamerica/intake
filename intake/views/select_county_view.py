"""Base classes for views that access session data and process intake forms
"""
from formation.forms import SelectCountyForm
from django.core.urlresolvers import reverse_lazy
from .applicant_form_mixin import ApplicantFormMixin
from intake import models

# transition visitor to applicant / fires app started event


class SelectCountyView(ApplicantFormMixin):
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def post(self, request, *args, **kwargs):

        # ApplicantService.add_applicant_to_request(request)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        models.ApplicationEvent.log_app_started(
            self.request.applicant,
            counties=form.parsed_data['counties'],
        )
        return super().form_valid(form)
