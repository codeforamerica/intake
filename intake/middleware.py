import logging
from urllib.parse import urlparse

from intake.models import Visitor
import intake.services.events_service as EventsService
import user_agents


logger = logging.getLogger(__name__)


def is_a_monitoring_request(request):
    """Returns True it the input request is for monitoring or health check
    purposes
    """
    # does the request begin with /health?
    return request.get_full_path()[:7] == '/health'


def is_a_valid_response_code(response):
    """Returns True if 200"""
    return response.status_code == 200


class MiddlewareBase:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(response)
        return response

    def process_request(self, request):
        return None

    def process_response(self, response):
        return None


class UserAgentMiddleware(MiddlewareBase):

    def process_request(self, request):
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        request.user_agent = user_agents.parse(user_agent_string)


class PersistReferrerMiddleware(MiddlewareBase):

    def process_request(self, request):
        if not is_a_monitoring_request(request):
            referrer = request.META.get('HTTP_REFERER')
            if referrer:
                referrer_host = urlparse(referrer).netloc
                # make sure this is not an internal referrer
                if referrer_host != request.get_host():
                    request.session['referrer'] = referrer
            return None


class PersistSourceMiddleware(MiddlewareBase):

    def process_request(self, request):
        if not is_a_monitoring_request(request):
            source = request.GET.get('source')
            if source:
                request.session['source'] = source


class GetCleanIpAddressMiddleware(MiddlewareBase):

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def process_request(self, request):
        if not is_a_monitoring_request(request):
            request.ip_address = self._get_client_ip(request)
            return None


class CountUniqueVisitorsMiddleware(MiddlewareBase):

    def __call__(self, request):
        if not is_a_monitoring_request(request):
            visitor_id = request.session.get('visitor_id', None)
            if not visitor_id:
                visitor = Visitor(
                    referrer=request.session.get('referrer', ''),
                    source=request.session.get('source', ''),
                    ip_address=getattr(request, 'ip_address', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    locale=getattr(request, 'LANGUAGE_CODE', ''))
                visitor.save()
                request.visitor = visitor
                EventsService.site_entered(visitor, request)
                request.session['visitor_id'] = visitor.id
            else:
                visitor = Visitor.objects.get(id=visitor_id)
                request.visitor = visitor
            response = self.get_response(request)

            if is_a_valid_response_code(response):
                response.view = None
                context_data = getattr(response, "context_data", {})
                if context_data:
                    response.view = context_data.get("view", None)
                if request.user.is_authenticated:
                    EventsService.user_page_viewed(request, response)
                else:
                    EventsService.page_viewed(request, response)
        else:
            response = self.get_response(request)
        return response
