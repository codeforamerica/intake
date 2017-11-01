from django import forms
from intake import models
from django.contrib.auth.models import User
from formation.display_form_base import DisplayForm
from formation.fields import (
    EmailField, PhoneNumberField, AddressField)


class StatusUpdateForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=User.objects.all())
    application = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=models.Application.objects.all())
    status_type = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=models.StatusType.objects.filter(
            is_active=True, is_a_status_update_choice=True
        ).order_by('display_order'),
        empty_label=None)
    next_steps = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
        queryset=models.NextStep.objects.filter(is_active=True))

    class Meta:
        model = models.StatusUpdate
        fields = [
            'author', 'application', 'status_type',
            'additional_information', 'next_steps', 'other_next_step']


class StatusNotificationForm(forms.ModelForm):
    sent_message = forms.CharField(
        widget=forms.Textarea())

    class Meta:
        model = models.StatusNotification
        fields = ['sent_message']


class NotificationContactInfoDisplayForm(DisplayForm):
    fields = [
        EmailField,
        PhoneNumberField,
        AddressField,
    ]
