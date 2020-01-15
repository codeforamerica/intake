"""
Views that redirect from old url patterns to new ones
"""
from django.views.generic import View
from django.shortcuts import redirect
from django.urls import reverse_lazy

from project.services.query_params import get_url_for_ids
from intake import models


class PermanentRedirectView(View):
    """Permanently redirects to a url
    by default, it will build a url from any kwargs
    self.build_redirect_url() can be overridden to provide logic
    """
    redirect_view_name = None

    def build_redirect_url(self, request, **kwargs):
        return reverse_lazy(
            self.redirect_view_name,
            kwargs=dict(**kwargs))

    def get(self, request, **kwargs):
        redirect_url = self.build_redirect_url(request, **kwargs)
        return redirect(redirect_url, permanent=True)


class SingleIdPermanentRedirect(PermanentRedirectView):
    """Redirects from
        sanfrancisco/0efd75e8721c4308a8f3247a8c63305d/
    to
        application/3/
    """

    def build_redirect_url(self, request, submission_id):
        submission = models.FormSubmission.objects.get(old_uuid=submission_id)
        return reverse_lazy(self.redirect_view_name,
                            kwargs=dict(submission_id=submission.id)
                            )


class MultiIdPermanentRedirect(PermanentRedirectView):
    """Redirects from
        sanfrancisco/bundle/?keys=0efd75e8721c4308a8f3247a8c63305d|b873c4ceb1cd4939b1d4c890997ef29c
    to
        applications/bundle/?ids=3,4
    """

    def build_redirect_url(self, request):
        key_set = request.GET.get('keys')
        uuids = [key for key in key_set.split('|')]
        submissions = models.FormSubmission.objects.filter(
            old_uuid__in=uuids)
        return get_url_for_ids(
            self.redirect_view_name,
            [s.id for s in submissions])
