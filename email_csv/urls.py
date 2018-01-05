from url_robots.utils import url
from . import views

urlpatterns = [
    url(r'^$', views.email_csv,
        name='email-csv', robots_allow=False),

]
