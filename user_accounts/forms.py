from django import forms
from invitations.forms import InviteForm as BaseInviteForm
from .models import Invitation, Organization

class InviteForm(BaseInviteForm):

    organization = forms.ModelChoiceField(
        label="Organization",
        required=True,
        queryset=Organization.objects.all(),
        empty_label=None)

    def save(self, inviter=None):
        return Invitation.create(
            email=self.cleaned_data['email'],
            organization=self.cleaned_data['organization'],
            inviter=inviter)

