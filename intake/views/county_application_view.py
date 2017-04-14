from intake import utils
from .applicant_form_view_base import ApplicantFormViewBase


class CountyApplicationWarningView(ApplicantFormViewBase):
    """County application page that does *not* check for validation warnings.
    """

    def get_form(self):
        session_data = utils.get_form_data_from_session(
            self.request, self.session_key)

        # get form
        pass

    def form_valid(self, form):
        # if needed, redirect to declaration letter
        if self.needs_declaration_letter(form):
            return redirect('intake-write_letter')
        # create and save new submission
        # send confirmations
        # log events
        return super().form_valid(self, form)


class CountyApplicationView(CountyApplicationWarningView):
    """County application page that checks for validation warnings.
    """
    def form_valid(self, form):
        # if form.warnings
        # return redirect to URL for warning page
        return super().form_valid(self, form)
