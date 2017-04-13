from django.views.generic.edit import FormView


class ApplicantFormMixin(FormView):

    def form_valid(self, form):
        # log that page was completed
        # save form data to session
        return super().form_valid(form)

    def form_invalid(self, form):
        # log validation errors
        return super().form_invalid(form)
