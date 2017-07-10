from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView


class LinkRedirectEventViewBase(RedirectView):
    """
    fires event to say that 
    a user arrived at unread through an email notification link.
    """

    def fire_event(self, request):
        print("Should fire an aevent hera")
        # fire event
        # self.event_func()

    def get(self, request):
        self.fire_event(request)
        return super().get(request)


class UnreadEmailRedirectView(LinkRedirectEventViewBase):
    url = reverse_lazy('intake-app_unread_index')
    event_func = 'nothing for now'


class NeedsUpdateEmailRedirectView(LinkRedirectEventViewBase):
    """Redirects to the Unread Apps Index, fires event to say that 
    a user arrived at unread through an email notification link.
    """
    url = reverse_lazy('intake-app_needs_update_index')
    event_func = 'nothing for now'


class AllEmailRedirectView(LinkRedirectEventViewBase):
    """Redirects to the Unread Apps Index, fires event to say that 
    a user arrived at unread through an email notification link.
    """
    url = reverse_lazy('intake-app_all_index')
    event_func = 'nothing for now'


unread_email_redirect = UnreadEmailRedirectView.as_view()
needs_update_email_redirect = NeedsUpdateEmailRedirectView.as_view()
unread_email_redirect = AllEmailRedirectView.as_view()
