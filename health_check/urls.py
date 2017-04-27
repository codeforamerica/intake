from django.conf.urls import url
from django.http import HttpResponse


def ok(request, *args, **kwargs):
    return HttpResponse("Everything seems fine", status=200)


def error(request, *args, **kwargs):
    return HttpResponse("Errors seem to work correctly", status=500)


urlpatterns = [
    url(r'^$', ok, name='health_check-ok'),
    url(r'^error$', error, name='health_check-error'),
]
