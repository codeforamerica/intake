from url_robots.utils import url
from .views import contact, home


urlpatterns = [
    url(r'^$', home, name='partnerships-home', robots_allow=True),
    url(r'^get-in-touch$',
        contact, name='partnerships-contact', robots_allow=True),
]
