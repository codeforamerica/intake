"""
Here are the important views in a rough order that follows the path of a
submission:

* `Home` - where a user would learn about the service and hit 'apply'
* `SelectCounty` - a user selects the counties they need help with. This stores
    the county selection in the session.
* `CountyApplication` - a dynamic form built based on the county selection data
    that was stored in the session. This view does most of the validation work.
* `Confirm` (maybe) - if warnings exist on the form, users will be directed
    here to confirm their submission. Unlike errors, warnings do not prevent
    submission. This is just a slightly reduced version of `CountyApplication`.
* `Thanks` - a confirmation page that shows data from the newly saved
    submission.

A daily notification is sent to organizations with a link to a bundle of their
new applications.

* `ApplicationBundle` - This is typically the main page that organization users
    will access. Here they will see a collection of new applications, and, if
    needed, can see a filled pdf for their intake forms. If they need a pdf
    it will be served in an iframe by `FilledPDFBundle`
* `ApplicationIndex` - This is a list page that lets an org user see all the
    applications to their organization, organized in a table. Here they can
    access links to `ApplicationDetail` and `FilledPDF` for each app.
* `ApplicationDetail` - This shows the detail of one particular FormSubmission
"""

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from intake import models, constants
from user_accounts.models import Organization
from user_accounts.forms import OrganizationDetailsDisplayForm


class Home(TemplateView):
    """Homepage view which shows information about the service
    """
    template_name = "main_splash.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if constants.SCOPE_TO_LIVE_COUNTIES:
            counties = models.County.objects.prefetch_related(
                'organizations').filter(slug__in=[
                    constants.Counties.SAN_FRANCISCO,
                    constants.Counties.CONTRA_COSTA])
        else:
            counties = models.County.objects.prefetch_related(
                'organizations').all()
        context['counties'] = counties
        return context


class PrivacyPolicy(TemplateView):
    template_name = "privacy_policy.jinja"


class PartnerListView(TemplateView):
    template_name = "partner_list.jinja"

    def get_context_data(self, *args, **kwargs):
        return dict(
            counties=models.County.objects.prefetch_related(
                'organizations').all())


class PartnerDetailView(TemplateView):
    template_name = "partner_detail.jinja"

    def get(self, request, organization_slug):
        self.organization_slug = organization_slug
        return super().get(request)

    def get_context_data(self, *args, **kwargs):
        query = Organization.objects.prefetch_related(
            'addresses'
            ).filter(
            is_receiving_agency=True
            )
        organization = get_object_or_404(
                query, slug=self.organization_slug)
        return dict(
            organization=organization,
            display_form=OrganizationDetailsDisplayForm(organization))


home = Home.as_view()
partner_list = PartnerListView.as_view()
partner_detail = PartnerDetailView.as_view()
privacy = PrivacyPolicy.as_view()
