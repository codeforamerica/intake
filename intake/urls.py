from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    url(r'^$', views.Home.as_view(), name='intake-home'),
    url(r'^apply/$', views.Apply.as_view(), name='intake-apply'),
    url(r'^thanks/$', views.Thanks.as_view(), name='intake-thanks'),
    url(r'^application/(?P<submission_id>[0-9]+)/$', 
        login_required(views.FilledPDF.as_view()), name='intake-filled_pdf'),
    url(r'^applications/$', 
        login_required(views.ApplicationIndex.as_view()),
        name='intake-app_index'),
]
