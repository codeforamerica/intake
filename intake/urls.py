from django.contrib.auth.decorators import login_required
from url_robots.utils import url
from intake.views import (
    public_views,
    stats_views,
    legacy_redirect_views,
    select_county_view,
    county_application_view,
    declaration_letter_view,
    application_done_view,
    application_transfer_view,
    admin_views,
    redirect_link_views,
    search_views,
    app_detail_views,
    application_note_views,
    tag_views,
    status_update_views,
    prebuilt_pdf_bundle_views,
    printout_views,
    data_export_views
)


def org_vs_staff_view_switch(org_user_view, staff_user_view):
    def switch(request, *args, **kwargs):
        if request.user.is_staff:
            return staff_user_view(request, *args, **kwargs)
        else:
            return org_user_view(request, *args, **kwargs)
    return switch


urlpatterns = [

    # PUBLIC VIEWS
    url(r'^$', public_views.home, name='intake-home', robots_allow=True),
    url(r'^privacy/$', public_views.privacy,
        name='intake-privacy', robots_allow=True),
    url(r'^partners/$', public_views.partner_list,
        name='intake-partner_list', robots_allow=True),
    url(r'^partners/(?P<organization_slug>[\w-]+)/$',
        public_views.partner_detail,
        name='intake-partner_detail', robots_allow=True),
    url(r'^recommendation-letters/$', public_views.recommendation_letters,
        name='intake-recommendation_letters', robots_allow=True),
    url(r'^personal-statement/$', public_views.personal_statement,
        name='intake-personal_statement', robots_allow=True),
    url(r'^stats/$', stats_views.stats,
        name='intake-stats', robots_allow=True),

    # PUBLIC FORM PROCESSING VIEWS
    url(r'^apply/$', select_county_view.select_county,
        name='intake-apply', robots_allow=True),
    url(r'^application/$', county_application_view.county_application,
        name='intake-county_application'),
    url(r'^application/letter/$',
        declaration_letter_view.write_letter, name='intake-write_letter'),
    url(r'^application/letter/review/$',
        declaration_letter_view.review_letter, name='intake-review_letter'),
    url(r'^confirm/$', county_application_view.confirm, name='intake-confirm'),
    url(r'^review/$', county_application_view.review, name='intake-review'),
    url(r'^thanks/$', application_done_view.thanks, name='intake-thanks'),
    url(r'^getting_your_rap/$', application_done_view.rap_sheet_info,
        name='intake-rap_sheet', robots_allow=True),


    # PROTECTED VIEWS
    url(r'^application/(?P<submission_id>[0-9]+)/$',
        login_required(app_detail_views.app_detail),
        name='intake-app_detail'),

    url(r'^application/(?P<submission_id>[0-9]+)/history/$',
        login_required(app_detail_views.app_history),
        name='intake-app_history'),

    url(r'^application/(?P<submission_id>[0-9]+)/pdf/$',
        login_required(admin_views.filled_pdf),
        name='intake-filled_pdf'),

    url(r'^application/(?P<submission_id>[0-9]+)/printout/$',
        login_required(printout_views.printout_for_submission),
        name='intake-case_printout'),

    url(r'^application/(?P<submission_id>[0-9]+)/transfer/$',
        login_required(application_transfer_view.transfer_application),
        name='intake-transfer_application'),

    # default applications view. Org users see unreads. Staff users see all
    url(r'^applications/$',
        login_required(
            org_vs_staff_view_switch(
                org_user_view=admin_views.app_unread_index,
                staff_user_view=admin_views.app_index)),
        name='intake-app_index'),

    url(r'^applications/unread/$',
        login_required(admin_views.app_unread_index),
        name='intake-app_unread_index'),

    url(r'^applications/needs_update/$',
        login_required(admin_views.app_needs_update_index),
        name='intake-app_needs_update_index'),

    url(r'^applications/county_not_listed/$',
        login_required(admin_views.app_cnl_index),
        name='intake-app_cnl_index'),

    url(r'^applications/all/$',
        login_required(admin_views.app_index),
        name='intake-app_all_index'),

    url(r'^applications-link/unread$',
        login_required(redirect_link_views.unread_email_redirect),
        name='intake-unread_email_redirect'),

    url(r'^applications-link/needs_update$',
        login_required(redirect_link_views.needs_update_email_redirect),
        name='intake-needs_update_email_redirect'),

    url(r'^applications-link/all$',
        login_required(redirect_link_views.all_email_redirect),
        name='intake-all_email_redirect'),

    # APPLICATION BUNDLE VIEWS
    url(r'^applications/unread/pdf/$',
        login_required(prebuilt_pdf_bundle_views.wrapper_view),
        name='intake-pdf_bundle_wrapper_view'),

    url(r'^applications/unread/pdf/prebuilt$',
        login_required(prebuilt_pdf_bundle_views.file_view),
        name='intake-pdf_bundle_file_view'),

    url(r'^applications/unread/pdf/printout$',
        login_required(printout_views.printout_for_apps),
        name='intake-pdf_printout_for_apps'),

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

    url(r'^applications/mark/processed/$',
        login_required(admin_views.mark_processed),
        name='intake-mark_processed'),

    url(r'^applications/(?P<submission_id>[0-9]+)/update-status/$',
        login_required(status_update_views.create_status_update),
        name='intake-create_status_update'),

    url(r'^applications/(?P<submission_id>[0-9]+)/review-status/$',
        login_required(status_update_views.review_status_notification),
        name='intake-review_status_notification'),

    url(r'^applications/csv-download',
        login_required(data_export_views.csv_download),
        name='intake-csv_download'),

    url(r'^applications-autocomplete/$', search_views.application_search,
        name='applications-autocomplete',),

    url(r'^followups-autocomplete/$', search_views.followup_search,
        name='followups-autocomplete',),

    # API Views
    url(r'^notes/create/$',
        login_required(application_note_views.create_note),
        name='intake-create_note'),

    url(r'^notes/(?P<pk>[0-9]+)/delete/$',
        login_required(application_note_views.destroy_note),
        name='intake-destroy_note'),

    url(r'^tags/add/$',
        login_required(tag_views.add_tags),
        name='intake-add_tags'),

    url(r'^tags/(?P<tag_id>[0-9]+)/remove/(?P<submission_id>[0-9]+)/$',
        login_required(tag_views.remove_tag),
        name='intake-remove_tag'),

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
