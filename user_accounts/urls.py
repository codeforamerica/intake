from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^signup/$', views.CustomSignupView.as_view(), name='user_accounts-signup'),
]
