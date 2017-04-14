from formation.forms import SelectCountyForm
from django.core.urlresolvers import reverse_lazy
from .applicant_form_view_base import ApplicantFormViewBase
import intake.services.applicants as ApplicantsService
import intake.services.events_service as EventsService


class SelectCountyView(ApplicantFormViewBase):
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def post(self, request, *args, **kwargs):
        ApplicantsService.create_new_applicant(request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        EventsService.log_app_started(
            self.request, counties=form.parsed_data['counties'])
        return super().form_valid(form)
