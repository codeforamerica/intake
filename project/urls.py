from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from robots_txt.views import robots_view


# Make sure to keep this up to date
allow = [
    '/$',
    '/apply/',
    '/stats/',
    '/partners/*',
    '/privacy/',
    '/personal-statement/',
    '/recommendation-letters/',
    '/gettings-your-rap/',
]

# Remember to update robots.txt above
urlpatterns = [
    url(r'^robots\.txt$', robots_view(allow)),
    url(r'^', include('intake.urls')),
    url(r'^', include('user_accounts.urls')),  # user account overrides
    url(r'^health/', include('health_check.urls')),
    url(r'^accounts/', include('allauth.urls')),  # user accounts
    url(r'^invitations/', include(
        'invitations.urls', namespace='invitations')),
    url(r'^admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# django debug toolbar
if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
