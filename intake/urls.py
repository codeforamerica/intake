from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # public views
    url(r'^$', views.home, name='intake-home'),
    url(r'^apply/$', views.apply_form, name='intake-apply'),
    url(r'^thanks/$', views.thanks, name='intake-thanks'),

    # protected views
    url(r'^application/(?P<submission_id>[0-9]+)/$', 
        login_required(views.filled_pdf),
        name='intake-filled_pdf'),
    
    url(r'^applications/$',
        login_required(views.app_index),
        name='intake-app_index'),

    url(r'^applications/bundle/$',
        login_required(views.app_bundle),
        name='intake-app_bundle'),

    url(r'^applications/pdfs/$',
        login_required(views.pdf_bundle),
        name='intake-pdf_bundle'),

    url(r'^application/(?P<submission_id>[0-9]+)/delete/$',
        login_required(views.delete_page),
        name='intake-delete_page'),
]
