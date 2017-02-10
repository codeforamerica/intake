from dal import autocomplete

from django import forms
from intake import models


class ApplicationSelectForm(forms.ModelForm):
    application = forms.ModelChoiceField(
        queryset=models.FormSubmission.objects.all(),
        widget=autocomplete.ModelSelect2(url='applicant-autocomplete')
    )

    class Meta:
        model = models.FormSubmission
        fields = ['anonymous_name']
        # fields = ('__all__')
