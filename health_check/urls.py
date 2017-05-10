from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse


def ok(request, *args, **kwargs):
    return HttpResponse("Everything seems fine", status=200)


@user_passes_test(lambda u: u.is_superuser)
def error(request, *args, **kwargs):
    raise Exception("This is a Test")


urlpatterns = [
    url(r'^$', ok, name='health_check-ok'),
    url(r'^error$', error, name='health_check-error'),
]
