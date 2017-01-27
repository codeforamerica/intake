from django import forms
from intake import models
from django.contrib.auth.models import User


class StatusUpdateForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=User.objects.all())
    application = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=models.Application.objects.all())
    status_type = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=models.StatusType.objects.filter(is_active=True))
    next_steps = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
        queryset=models.NextStep.objects.filter(is_active=True))

    class Meta:
        model = models.StatusUpdate
        fields = [
            'author', 'application', 'status_type',
            'additional_information', 'next_steps', 'other_next_step']
