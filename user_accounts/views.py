import json

from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from allauth.account import views as allauth_views
from invitations.views import SendInvite

from intake.services.mailgun_api_service import is_a_valid_mailgun_post
from . import forms
from user_accounts.base_views import StaffOnlyMixin
import intake.services.events_service as EventsService


class CustomLoginView(allauth_views.LoginView):
    template_name = "user_accounts/login.jinja"

    def get_form_class(self):
        return forms.LoginForm

    def form_invalid(self, *args):
        # get the email entered, if it exists
        login_email = self.request.POST.get('login', '')
        # save it in the session, in case the go to password reset
        if login_email:
            self.request.session['failed_login_email'] = login_email
        EventsService.user_failed_login(self)
        return super().form_invalid(*args)


class CustomSignupView(allauth_views.SignupView):
    template_name = "user_accounts/signup.jinja"

    def get_form_class(self):
        return forms.CustomSignUpForm

    def closed(self):
        return redirect('intake-home')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user = self.user
        EventsService.user_account_created(self)
        return response


class CustomSendInvite(StaffOnlyMixin, SendInvite):
    template_name = "user_accounts/invite_form.jinja"
    form_class = forms.InviteForm
    success_url = reverse_lazy("user_accounts-profile")

    def form_valid(self, form):
        invite = form.save(inviter=self.request.user)
        invite.send_invitation(self.request)
        messages.success(self.request,
                         'An email invite was sent to {}'.format(invite.email))
        return redirect(self.success_url)


class UserProfileView(FormView):
    template_name = "user_accounts/userprofile_form.jinja"
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
        EventsService.user_login(self)
        return context

    def form_valid(self, form, *args, **kwargs):
        profile = self.request.user.profile
        profile.name = form.cleaned_data['name']
        profile.save()
        return super().form_valid(form)


class PasswordResetView(allauth_views.PasswordResetView):
    template_name = 'user_accounts/request_password_reset.jinja'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # if there is an login email in the session
        login_email = self.request.session.get('failed_login_email', '')
        initial_email = context['form'].initial.get('email', '')
        if not initial_email:
            context['form'].initial['email'] = login_email
        EventsService.user_reset_password(self, initial_email)
        return context


class PasswordResetSentView(allauth_views.PasswordResetDoneView):
    template_name = 'user_accounts/password_reset_sent.jinja'


class PasswordResetFromKeyView(allauth_views.PasswordResetFromKeyView):
    template_name = 'user_accounts/change_password.jinja'

    def get_form_class(self):
        return forms.SetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_user'] = getattr(self, 'reset_user', None)
        return context


class PasswordChangeView(allauth_views.PasswordChangeView):
    template_name = 'user_accounts/change_password.jinja'
    success_url = reverse_lazy("user_accounts-profile")

    def get_form_class(self):
        return forms.SetPasswordForm


class MailgunBouncedEmailView(View):

    def post(self, request):
        if not is_a_valid_mailgun_post(request):
            raise Http404
        to = request.POST['recipient']
        error = request.POST['error']
        headers = dict(json.loads(request.POST['message-headers']))
        sender = headers['Sender']
        subject = headers['Subject']
        date = headers['Date']
        bounce_message = """
A notification you sent through Clear My Record could not be delivered.

Date: {date}
Applicant email: {to}
Email subject: {subject}

Error:
{error}


Let us know if you have any questions,

Clear My Record Team
clearmyrecord@codeforamerica.org
""".format(date=date, to=to, subject=subject, error=error)
        send_mail(
            subject='Clear My Record: An applicant notification bounced',
            message=bounce_message,
            html_message=bounce_message.replace('\n', '<br>'),
            from_email=settings.MAIL_DEFAULT_SENDER,
            recipient_list=[sender],
            fail_silently=False)
        return HttpResponse()
