"""
This module handles queries to retrieve common statistics
"""
from intake import models, constants
from collections import Counter

TOTAL = 'Total'
ALL = (constants.Organizations.ALL, 'Total (All Organizations)')


def get_status_update_success_metrics():
    """
    Returns the total and statustype totals of status updates and notifications
        total & by org
        'updates' {
            'all': Counter(
                'Total': 23,
                'No Convictions': 4,
                'Eligible': 6,


            }
        }
    """
    updates = models.StatusUpdate.objects.all().prefetch_related(
        'application__organization',
        'status_type'
    )
    orgs = {ALL: Counter()}
    for update in updates:
        org = (
            update.application.organization.slug,
            update.application.organization.name
        )
        status_type = update.status_type.display_name
        if not orgs.get(org):
            orgs[org] = Counter()
        orgs[ALL].update([TOTAL, status_type])
        orgs[org].update([TOTAL, status_type])
    data = []
    sorted_orgs = sorted(
        orgs.items(),
        key=lambda entry: constants.DEFAULT_ORGANIZATION_ORDER.index(
            entry[0][0])
        )
    for org_tuple, counter in sorted_orgs:
        entry = (
            org_tuple[1],
            list(sorted(
                counter.items(),
                key=lambda n: n[1],
                reverse=True
            ))
        )
        data.append(entry)
    return data
