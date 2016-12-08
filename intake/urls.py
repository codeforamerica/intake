from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from intake.views import (
    public_views,
    stats_views,
    legacy_redirect_views,
    application_form_views,
    admin_views,
    followup_views,
    )

urlpatterns = [
    # public views
    url(r'^$', public_views.home, name='intake-home'),
    url(r'^privacy/$', public_views.privacy, name='intake-privacy'),
    url(r'^partners/$', public_views.partner_list, name='intake-partner_list'),
    url(r'^partners/(?P<organization_slug>[\w-]+)/$',
        public_views.partner_detail, name='intake-partner_detail'),

    # public form processing views
    url(r'^apply/$',
        application_form_views.select_county, name='intake-apply'),
    url(r'^application/$', application_form_views.county_application,
        name='intake-county_application'),
    url(r'^application/letter/$',
        application_form_views.write_letter, name='intake-write_letter'),
    url(r'^application/letter/review/$',
        application_form_views.review_letter, name='intake-review_letter'),
    url(r'^confirm/$', application_form_views.confirm, name='intake-confirm'),
    url(r'^thanks/$', application_form_views.thanks, name='intake-thanks'),
    url(r'^getting_your_rap/$',
        application_form_views.rap_sheet_info, name='intake-rap_sheet'),

    # stats views
    url(r'^stats/$', stats_views.stats, name='intake-stats'),

    # protected views
    url(r'^application/(?P<submission_id>[0-9]+)/$',
        login_required(admin_views.app_detail),
        name='intake-app_detail'),

    url(r'^application/(?P<submission_id>[0-9]+)/pdf/$',
        login_required(admin_views.filled_pdf),
        name='intake-filled_pdf'),

    url(r'^application/(?P<submission_id>[0-9]+)/printout/$',
        login_required(admin_views.case_printout),
        name='intake-case_printout'),

    url(r'^applications/$',
        login_required(admin_views.app_index),
        name='intake-app_index'),

    url(r'^applications/bundle/$',
        login_required(admin_views.app_bundle),
        name='intake-app_bundle'),

    url(r'^applications/bundle/(?P<bundle_id>[0-9]+)/$',
        login_required(admin_views.app_bundle_detail),
        name='intake-app_bundle_detail'),

    url(r'^applications/bundle/(?P<bundle_id>[0-9]+)/pdf/$',
        login_required(admin_views.app_bundle_detail_pdf),
        name='intake-app_bundle_detail_pdf'),

    url(r'^applications/bundle/(?P<bundle_id>[0-9]+)/printout/$',
        login_required(admin_views.case_bundle_printout),
        name='intake-case_bundle_printout'),

    url(r'^applications/pdfs/$',
        login_required(admin_views.pdf_bundle),
        name='intake-pdf_bundle'),

    url(r'^application/(?P<submission_id>[0-9]+)/delete/$',
        login_required(admin_views.delete_page),
        name='intake-delete_page'),

    url(r'^applications/mark/processed/$',
        login_required(admin_views.mark_processed),
        name='intake-mark_processed'),

    url(r'^applications/mark/transferred/$',
        login_required(admin_views.mark_transferred_to_other_org),
        name='intake-mark_transferred_to_other_org'),


    url(r'^followups/$',
        login_required(followup_views.index),
        name='intake-followups'),

]

redirects = [
    url(r'^sanfrancisco/$',
        legacy_redirect_views.PermanentRedirectView.as_view(
            redirect_view_name='intake-apply')),
    url(r'^sanfrancisco/applications/$',
        legacy_redirect_views.PermanentRedirectView.as_view(
            redirect_view_name='intake-app_index')),
    # https://regex101.com/r/wO1pD3/1
    url(r'^sanfrancisco/(?P<submission_id>[0-9a-f]{32})/$',
        legacy_redirect_views.SingleIdPermanentRedirect.as_view(
            redirect_view_name='intake-filled_pdf')),
    url(r'^sanfrancisco/bundle/$',
        legacy_redirect_views.MultiIdPermanentRedirect.as_view(
            redirect_view_name='intake-app_bundle')),
    url(r'^sanfrancisco/pdfs/$',
        legacy_redirect_views.MultiIdPermanentRedirect.as_view(
            redirect_view_name='intake-pdf_bundle')),
]

urlpatterns += redirects
