from django.contrib.auth.mixins import PermissionRequiredMixin
from intake import permissions
import intake.services.counties as CountiesService


class GlobalTemplateContextMixin:

    def get_context_data(self):
        context = super().get_context_data()
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        context.update(
            counties=counties,
            all_county_names='counties throughout California',
            organizations=orgs
        )
        return context


class ViewAppDetailsMixin(PermissionRequiredMixin):
    permission_required = 'intake.' + permissions.CAN_SEE_APP_DETAILS
