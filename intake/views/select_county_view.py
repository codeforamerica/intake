from formation.forms import SelectCountyForm
from django.urls import reverse_lazy
from .applicant_form_view_base import ApplicantFormViewBase
import intake.services.applicants as ApplicantsService
import intake.services.events_service as EventsService


class SelectCountyView(ApplicantFormViewBase):
    form_class = SelectCountyForm
    template_name = "forms/county_selection.jinja"
    success_url = reverse_lazy('intake-county_application')

    def check_for_session_based_redirects(self):
        """disable ApplicantFormViewBase's check for 'counties' in the session
            data
        """
        pass

    def post(self, request, *args, **kwargs):
        ApplicantsService.create_new_applicant(request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        EventsService.form_started(
            self, counties=form.parsed_data['counties'])
        return super().form_valid(form)


select_county = SelectCountyView.as_view()
