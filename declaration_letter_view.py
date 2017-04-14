from .applicant_form_view_base import ApplicantFormViewBase
from django.core.urlresolvers import reverse_lazy


class WriteDeclarationLetterView(ApplicantFormViewBase):
    template_name = "forms/declaration_letter_form.jinja"
    success_url = reverse_lazy('intake-review_letter')

    def get_form(self):
        # get the declaration letter form
        pass


class ReviewDeclarationLetterView(ApplicantFormViewBase):
    template_name = "forms/declaration_letter_review.jinja"
    success_url = reverse_lazy('intake-thanks')

    def form_valid(self):
        self.finalize_application()
        return super().form_valid()
