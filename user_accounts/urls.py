from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^accounts/signup/$', views.CustomSignupView.as_view(), name='user_accounts-signup'),
    url(r'^invitations/send-invite/$', views.CustomSendInvite.as_view(), name='user_accounts-send_invite'),
]
