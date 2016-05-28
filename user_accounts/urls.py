from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    url(r'^accounts/login/$',
        views.CustomLoginView.as_view(),
        name = 'user_accounts-login'),
    url(r'^accounts/profile/$',
        login_required(views.UserProfileView.as_view()),
        name='user_accounts-profile'),
    url(r'^accounts/signup/$',
        views.CustomSignupView.as_view(),
        name='user_accounts-signup'),
    url(r'^invitations/send-invite/$',
        login_required(views.CustomSendInvite.as_view()),
        name='user_accounts-send_invite'),
]
