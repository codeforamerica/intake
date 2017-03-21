from django import forms
from django.utils.translation import ugettext_lazy as _
from intake import models
from user_accounts.models import Organization


class ApplicationTransferForm(forms.ModelForm):

    next_url = forms.CharField(
        widget=forms.HiddenInput, required=False)
    to_organization = forms.ModelChoiceField(
        label=_('Transfer to'),
        widget=forms.RadioSelect(),
        queryset=Organization.objects.all(),
        empty_label=None)
    reason = forms.CharField(
        label=_("Why are you transferring this application?"),
        required=False,
        help_text=_(
            "This will only be visible to staff at the receiving "
            "organization"),
        widget=forms.Textarea())
    sent_message = forms.CharField()

    class Meta:
        model = models.ApplicationTransfer
        fields = ['to_organization', 'reason', 'sent_message', 'next_url']
