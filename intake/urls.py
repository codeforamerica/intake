from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.Home.as_view(), name='intake-home'),
    url(r'^apply/$', views.Apply.as_view(), name='intake-apply'),
    url(r'^thanks/$', views.Thanks.as_view(), name='intake-thanks'),
]
