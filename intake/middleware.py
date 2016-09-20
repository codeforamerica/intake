from urllib.parse import urlparse


class PersistReferrerMiddleware:

    def process_request(self, request):

        referrer = request.META.get('HTTP_REFERER')
        if referrer:
            referrer_host = urlparse(referrer).netloc
            if referrer_host != request.get_host():
                request.session['referrer'] = referrer

        return None
