from .applicant_form_mixin import ApplicantFormMixin


class CountyApplicationWarning(ApplicantFormMixin):
    def get_form(self):
        # get counties
        # get form

    def form_valid(self, form):
        # create and save new submission
        # send confirmations
        # log events
        return super().form_valid(self, form)


class CountyApplication(CountyApplicationWarning):
    def form_valid(self, form):
        # if form.warnings
        # return redirect to URL for warning page
        return super().form_valid(self, form)
