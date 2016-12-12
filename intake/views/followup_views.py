from django.views.generic.base import TemplateView
from user_accounts.base_views import StaffOnlyMixin

import intake.services.followups as FollowupsService


class FollowupsIndex(StaffOnlyMixin, TemplateView):
    template_name = "application_set.jinja"
    heading = "Applications Due for Followups"
    empty_set_message = "All caught up! :)"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        count, subs = FollowupsService.serialized_follow_up_subs()
        context['submissions'] = subs
        context['count'] = count
        context['page_heading'] = self.heading
        context['empty_set_message'] = self.empty_set_message
        return context


index = FollowupsIndex.as_view()
