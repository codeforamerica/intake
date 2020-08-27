from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django2_url_robots.views import robots_txt
from django.views.generic import TemplateView

if settings.MAINTENANCE_MODE:
    urlpatterns = [
        url(r'^', TemplateView.as_view(template_name='maintenance.html')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns = [
        url(r'^robots\.txt$', robots_txt),
        url(r'^', include('intake.urls')),
        # user account overrides
        url(r'^', include('user_accounts.urls')),
        url(r'^phone/', include('phone.urls')),
        url(r'^partnerships/', include('partnerships.urls')),
        url(r'^health/', include('health_check.urls')),
        url(r'^accounts/', include('allauth.urls')),  # user accounts
        url(r'^invitations/', include(
            'invitations.urls', namespace='invitations')),
        url(r'^admin/', admin.site.urls),
        url(r'^clips/', include('clips.urls')),
        url(r'^email_csv/', include('email_csv.urls')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
