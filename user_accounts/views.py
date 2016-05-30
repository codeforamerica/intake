from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from allauth.account import views as allauth_views
from invitations.views import SendInvite

from . import forms, models


class CustomLoginView(allauth_views.LoginView):

    def get_form_class(self):
        return forms.LoginForm

    def form_invalid(self, *args):
        # get the email entered, if it exists
        login_email = self.request.POST.get('login', '')
        # save it in the session, in case the go to password reset
        if login_email:
            self.request.session['failed_login_email'] = login_email
        return super().form_invalid(*args)


class CustomSignupView(allauth_views.SignupView):
    template_name = "user_accounts/signup.html"

    def get_form_class(self):
        return forms.CustomSignUpForm

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


class PasswordResetView(allauth_views.PasswordResetView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # if there is an login email in the session
        login_email = self.request.session.get('failed_login_email', '')
        initial_email = context['form'].initial.get('email', '')
        if not initial_email:
            context['form'].initial['email'] = login_email
        return context


class PasswordResetFromKeyView(allauth_views.PasswordResetFromKeyView):
    template_name = 'user_accounts/change_password.html'
 
    def get_form_class(self):
        return forms.SetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_user'] = getattr(self, 'reset_user', None)
        return context

class PasswordChangeView(allauth_views.PasswordChangeView):
    template_name = 'user_accounts/change_password.html'
    success_url = reverse_lazy("user_accounts-profile")

    def get_form_class(self):
        return forms.SetPasswordForm


