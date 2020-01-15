from django2_url_robots.utils import url
from . import views

urlpatterns = [
    url(r'^$', views.ClipCreateView.as_view(),
        name='clips-create', robots_allow=False),
    url(r'^(?P<pk>[0-9]+)/$', views.ClipUpdateView.as_view(),
        name='clips-update', robots_allow=False),
    url(r'^(?P<pk>[0-9]+)/delete$', views.ClipDeleteView.as_view(),
        name='clips-delete', robots_allow=False),
]
