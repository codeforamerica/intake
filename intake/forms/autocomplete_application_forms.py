from dal import autocomplete

from django import forms
from intake import models


class ApplicationSelectForm(forms.ModelForm):
    application = forms.ModelChoiceField(
        queryset=models.Application.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='applicant-autocomplete',
            attrs={'data-html': 'true'})
    )

    class Meta:
        model = models.Application
        fields = ('__all__')
