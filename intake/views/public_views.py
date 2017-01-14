
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, When
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
                    constants.Counties.CONTRA_COSTA,
                    constants.Counties.ALAMEDA,
                    constants.Counties.MONTEREY,
                    ])
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
        counties = models.County.objects.annotate(
            live_org_count=Count(
                Case(When(
                    organizations__is_accepting_applications=True, then=1
                ))
            )
        ).filter(live_org_count__gte=1).prefetch_related('organizations')
        return dict(counties=counties)


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
