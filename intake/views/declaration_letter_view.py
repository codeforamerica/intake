from .applicant_form_view_base import ApplicantFormViewBase
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from formation.forms import (
    DeclarationLetterFormSpec, DeclarationLetterDisplay,
    DeclarationLetterReviewForm, county_form_selector)
from django.utils import timezone
from intake.constants import (APPROVE_LETTER, EDIT_LETTER)


letter_form_spec = DeclarationLetterFormSpec()


class WriteDeclarationLetterView(ApplicantFormViewBase):
    template_name = "forms/declaration_letter_form.jinja"
    success_url = reverse_lazy('intake-review_letter')
    form_class = letter_form_spec.build_form_class()


class ReviewDeclarationLetterView(ApplicantFormViewBase):
    template_name = "forms/declaration_letter_review.jinja"
    success_url = reverse_lazy('intake-thanks')

    def get_form(self):
        if self.request.method == 'GET':
            display_data = self.session_data.copy()
            display_data['date_received'] = timezone.now()
            return DeclarationLetterDisplay(display_data, validate=True)
        elif self.request.method in ('POST', 'PUT'):
            return DeclarationLetterReviewForm(data=self.request.POST)

    def form_valid(self, form):
        answer = form.cleaned_data['submit_action']
        if answer == EDIT_LETTER:
            return redirect(reverse('intake-write_letter'))
        elif answer == APPROVE_LETTER:
            # build a complete form that combines the letter and county forms
            county_form_spec = county_form_selector.get_combined_form_spec(
                counties=self.county_slugs)
            full_form_spec = county_form_spec | letter_form_spec
            Form = full_form_spec.build_form_class()
            full_form = Form(self.session_data, validate=True)
            self.finalize_application(full_form)
        return super().form_valid(form)


write_letter = WriteDeclarationLetterView.as_view()
review_letter = ReviewDeclarationLetterView.as_view()
