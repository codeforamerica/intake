from django import forms
from invitations.forms import InviteForm as BaseInviteForm
from . import models, exceptions


class InviteForm(BaseInviteForm):

    organization = forms.ModelChoiceField(
        label="Organization",
        required=True,
        queryset=models.Organization.objects.all(),
        empty_label=None)

    def save(self, inviter=None):
        return models.Invitation.create(
            email=self.cleaned_data['email'],
            organization=self.cleaned_data['organization'],
            inviter=inviter)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ['name']


class CustomSignUpForm(forms.Form):
    name = forms.CharField(max_length=200, label='Name',
        required=False)

    def signup(self, request, user):
        user = models.UserProfile.create_from_invited_user(
            user=user,
            name=self.cleaned_data['name']
            )