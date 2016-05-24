from django.shortcuts import redirect
from allauth.account.views import SignupView
from invitations.views import SendInvite

from . import forms


class CustomSignupView(SignupView):

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