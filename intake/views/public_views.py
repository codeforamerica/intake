
from django.shortcuts import get_object_or_404
from intake.views.base_views import GlobalTemplateContextMixin
from django.views.generic.base import TemplateView
from user_accounts.models import Organization
from user_accounts.forms import OrganizationDetailsDisplayForm


class Home(GlobalTemplateContextMixin, TemplateView):
    """Homepage view which shows information about the service
    """
    template_name = "main_splash.jinja"


class PrivacyPolicy(GlobalTemplateContextMixin, TemplateView):
    template_name = "privacy_policy.jinja"


class PartnerListView(GlobalTemplateContextMixin, TemplateView):
    template_name = "partner_list.jinja"


class PartnerDetailView(GlobalTemplateContextMixin, TemplateView):
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


class RecommendationLettersView(GlobalTemplateContextMixin, TemplateView):
    template_name = "packet_instructions.jinja"


class PersonalStatementView(GlobalTemplateContextMixin, TemplateView):
    template_name = "personal_statement_instructions.jinja"

home = Home.as_view()
partner_list = PartnerListView.as_view()
partner_detail = PartnerDetailView.as_view()
privacy = PrivacyPolicy.as_view()
recommendation_letters = RecommendationLettersView.as_view()
personal_statement = PersonalStatementView.as_view()
