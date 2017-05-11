import logging
from urllib.parse import urlparse

from intake.models import Visitor
import intake.services.events_service as EventsService


logger = logging.getLogger(__name__)


class PersistReferrerMiddleware:

    def process_request(self, request):
        referrer = request.META.get('HTTP_REFERER')
        if referrer:
            referrer_host = urlparse(referrer).netloc
            # make sure this is not an internal referrer
            if referrer_host != request.get_host():
                request.session['referrer'] = referrer
        return None


class PersistSourceMiddleware:

    def process_request(self, request):
        source = request.GET.get('source')
        if source:
            request.session['source'] = source


class GetCleanIpAddressMiddleware:

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def process_request(self, request):
        request.ip_address = self._get_client_ip(request)
        return None


class CountUniqueVisitorsMiddleware:

    def process_request(self, request):
        visitor_id = request.session.get(
            'visitor_id', None)
        if not visitor_id:
            visitor = Visitor(
                referrer=request.session.get('referrer', ''),
                source=request.session.get('source', ''),
                ip_address=getattr(request, 'ip_address', '')
            )
            visitor.save()
            EventsService.site_entered(visitor, request.get_full_path())
            request.session['visitor_id'] = visitor.id
        else:
            visitor = Visitor.objects.get(id=visitor_id)
            EventsService.page_viewed(visitor, request.get_full_path())
        request.visitor = visitor
