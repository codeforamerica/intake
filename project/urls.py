from django.http import HttpResponse
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin


robots_txt = """User-agent: *
Disallow: /admin
Disallow: /health/
Disallow: /invitations/
Disallow: /accounts/
Disallow: %s
""" % (settings.STATIC_URL,)

urlpatterns = [
    url(r'^', include('intake.urls')),
    # user account overrides
    url(r'^', include('user_accounts.urls')),
    # user accounts
    url(r'^health/', include('health_check.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^invitations/', include(
        'invitations.urls', namespace='invitations')),
    url(r'^admin/', admin.site.urls),
    url(r'^robots\.txt$', lambda r: HttpResponse(
        robots_txt, content_type='text/plain')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# django debug toolbar
if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
