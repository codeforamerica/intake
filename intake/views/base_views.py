from django.shortcuts import redirect
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.contrib import messages
from project import alerts
from project.services import query_params
from project.exceptions import InvalidQueryParamsError
from intake import permissions
import intake.services.counties as CountiesService
from user_accounts.models import Organization


class GlobalTemplateContextMixin:

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        context.update(
            counties=counties,
            all_county_names='counties throughout California',
            organizations=orgs
        )
        return context


class ViewAppDetailsMixin(PermissionRequiredMixin):
    permission_required = 'intake.' + permissions.CAN_SEE_APP_DETAILS

    def handle_no_permission(self):
        return not_allowed(self.request)


class NoBrowserCacheOnGetMixin:
    """Sets the 'Cache-Control' response header to
        'no-cache, max-age=0, must-revalidate, no-store'
    on GET requests.

    This is useful if you would like the browser to refetch
    the page when a user navigates to it using the Back button.
    """
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response['Cache-Control'] = \
            'no-cache, max-age=0, must-revalidate, no-store'
        return response


class AppIDQueryParamMixin:
    """
    A base view for ApplicationsListViews that retrieve resources using a list
    of Application IDs in query params.
        /some_url?ids=12,43,23,54,43
    """
    def request_valid(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def handle_empty_list_request(self, request, *args, **kwargs):
        redirect_url = reverse('intake-app_index')
        alert_subject = \
            'Warning: "{}" ({}) accessed with no application IDs'.format(
                request.get_full_path(), self.__class__.__name__)
        alert_message = '{} <{}> was redirected to "{}"'.format(
            request.user.profile.name, request.user.email, redirect_url)
        alerts.send_email_to_admins(
            subject=alert_subject, message=alert_message)
        return redirect(reverse('intake-app_index'))

    def get(self, request, *args, **kwargs):
        try:
            self.app_ids = query_params.get_ids_from_query_params(request)
        except InvalidQueryParamsError as err:
            return not_allowed(request)
        self.request = request
        self.profile = request.user.profile
        linked_organizations = list(Organization.objects.filter(
            applications__id__in=self.app_ids).distinct())
        if len(linked_organizations) != 1:
            return not_allowed(request)
        self.organization = linked_organizations[0]
        has_access = request.user.is_staff or (
            self.profile.organization == self.organization)
        if not has_access:
            return not_allowed(request)
        else:
            if not self.app_ids:
                return self.handle_empty_list_request(request, *args, **kwargs)
            return self.request_valid(request, *args, **kwargs)


NOT_ALLOWED_MESSAGE = str(
    "Sorry, there was something wrong with that link. "
    "If you have any questions, please contact us at "
    "clearmyrecord@codeforamerica.org")

NOT_ALLOWED_ADMIN_ALERT_MESSAGE = str(
    "{user_email} attempted to access {url}, "
    "which they are not currently permitted to view. "
    "They were redirected to '{redirect_view}' and given the "
    "error message:\n\n{flash_message}\n\n"
    "Additional Error Info:\n{error_messages}")


def not_allowed(
        request, redirect_view='user_accounts-profile', error_messages='None'):
    messages.error(request, NOT_ALLOWED_MESSAGE)
    alerts.send_email_to_admins(
        subject="A user attempted to access an unpermitted URL",
        message=NOT_ALLOWED_ADMIN_ALERT_MESSAGE.format(
            user_email=getattr(request.user, 'email', 'No email'),
            url=request.get_full_path(),
            redirect_view=redirect_view,
            flash_message=NOT_ALLOWED_MESSAGE,
            error_messages=error_messages))
    return redirect(redirect_view)
