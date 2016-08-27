from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # public views
    url(r'^$', views.home, name='intake-home'),
    url(r'^apply/$', views.select_county, name='intake-apply'),
    url(r'^application/$', views.county_application,
        name='intake-county_application'),
    url(r'^confirm/$', views.confirm, name='intake-confirm'),
    url(r'^thanks/$', views.thanks, name='intake-thanks'),
    url(r'^stats/$', views.stats, name='intake-stats'),
    url(r'^privacy/$', views.privacy, name='intake-privacy'),

    # protected views
    url(r'^application/(?P<submission_id>[0-9]+)/$',
        login_required(views.app_detail),
        name='intake-app_detail'),

    url(r'^application/(?P<submission_id>[0-9]+)/pdf/$',
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

    url(r'^applications/mark/processed/$',
        login_required(views.mark_processed),
        name='intake-mark_processed'),
]

redirects = [
    url(r'^sanfrancisco/$',
        views.PermanentRedirectView.as_view(
            redirect_view_name='intake-apply')),
    url(r'^sanfrancisco/applications/$',
        views.PermanentRedirectView.as_view(
            redirect_view_name='intake-app_index')),
    # https://regex101.com/r/wO1pD3/1
    url(r'^sanfrancisco/(?P<submission_id>[0-9a-f]{32})/$',
        views.SingleIdPermanentRedirect.as_view(
            redirect_view_name='intake-filled_pdf')),
    url(r'^sanfrancisco/bundle/$',
        views.MultiIdPermanentRedirect.as_view(
            redirect_view_name='intake-app_bundle')),
    url(r'^sanfrancisco/pdfs/$',
        views.MultiIdPermanentRedirect.as_view(
            redirect_view_name='intake-pdf_bundle')),
]

urlpatterns += redirects
