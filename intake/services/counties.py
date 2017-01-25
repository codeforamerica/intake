from user_accounts.models import Organization
from intake.models import County


def get_live_counties_and_orgs():
    live_orgs = Organization.objects.filter(
        is_live=True, is_receiving_agency=True)
    live_counties = County.objects.filter(
        organizations__in=live_orgs).distinct()
    return live_counties, live_orgs
