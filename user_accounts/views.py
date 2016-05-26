from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from allauth.account.views import SignupView
from invitations.views import SendInvite

from . import forms, models


class CustomSignupView(SignupView):
    template_name = "user_accounts/signup.html"

    def closed(self):
        return redirect('intake-home')


class CustomSendInvite(SendInvite):
    template_name = "user_accounts/invite_form.html"
    form_class = forms.InviteForm

    def form_valid(self, form):
        invite = form.save(inviter=self.request.user)
        invite.send_invitation(self.request)
        return self.render_to_response(
            self.get_context_data(
                success_message='%s has been invited' % invite.email))


class UserProfileView(FormView):
    template_name = "user_accounts/userprofile_form.html"
    form_class = forms.UserProfileForm
    success_url = reverse_lazy("user_accounts-profile")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.profile = None

    def get_user_and_profile(self):
        self.user = self.user or self.request.user
        self.profile = self.profile or self.user.profile

    def get_initial(self):
        self.get_user_and_profile()
        return {
            'name': self.profile.name
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_user_and_profile()
        context.update(
            user=self.user, profile=self.profile)
        return context

    def form_valid(self, form, *args, **kwargs):
        profile = self.request.user.profile
        profile.name = form.cleaned_data['name']
        profile.save()
        return super().form_valid(form)




