from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
import intake.services.events_service as EventsService


class LinkRedirectEventViewBase(RedirectView):
    """
    fires event to say that
    a user arrived at unread through an email notification link.
    """

    def fire_event(self):
        EventsService.user_email_link_clicked(self)

    def get(self, request):
        self.request = request
        self.fire_event()
        return super().get(request)


class UnreadEmailRedirectView(LinkRedirectEventViewBase):
    """Redirects to the Unread Apps Index"""
    url = reverse_lazy('intake-app_unread_index')


class NeedsUpdateEmailRedirectView(LinkRedirectEventViewBase):
    """Redirects to the Needs Update Apps Index"""
    url = reverse_lazy('intake-app_needs_update_index')


class AllEmailRedirectView(LinkRedirectEventViewBase):
    """Redirects to the All Apps Index"""
    url = reverse_lazy('intake-app_all_index')


unread_email_redirect = UnreadEmailRedirectView.as_view()
needs_update_email_redirect = NeedsUpdateEmailRedirectView.as_view()
all_email_redirect = AllEmailRedirectView.as_view()
