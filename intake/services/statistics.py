"""
This module handles queries to retrieve common statistics
"""
from intake import models, constants
from collections import Counter

TOTAL = 'Total'
ALL = (constants.Organizations.ALL, 'Total (All Organizations)')


def get_status_update_success_metrics():
    """calculates the total number of status updates,
        including the totals by type of status for all orgs and each org.

    Example output:

    [('Total (All Organizations)',
      [('Total', 20),
       ('Eligible', 3),
       ('Passed', 3),
       ('No Convictions', 3),
       ('Court Date', 3),
       ("Can't Proceed", 3),
       ('Not Eligible', 3),
       ('Declined', 2)]),
     ('San Francisco Public Defender',
      [('Total', 2), ('Declined', 1), ("Can't Proceed", 1)]),
     ("Alameda County Public Defender's Office",
      [('Total', 2), ('Eligible', 1), ('Not Eligible', 1)]),
     ('East Bay Community Law Center',
      [('Total', 2), ('Passed', 1), ('Court Date', 1)]),
     ('Contra Costa Public Defender',
      [('Total', 2), ("Can't Proceed", 1), ('No Convictions', 1)]),
     ('Monterey County Public Defender',
      [('Total', 2), ('No Convictions', 1), ('Not Eligible', 1)]),
     ('Solano County Public Defender',
      [('Total', 2), ('Eligible', 1), ('Court Date', 1)]),
     ('San Diego County Public Defender',
      [('Total', 2), ('Passed', 1), ('Declined', 1)]),
     ('San Joaquin County Public Defender',
      [('Total', 2), ("Can't Proceed", 1), ('No Convictions', 1)]),
     ('Santa Clara County Public Defender',
      [('Total', 2), ('Eligible', 1), ('Not Eligible', 1)]),
     ('Fresno County Public Defender',
      [('Total', 2), ('Passed', 1), ('Court Date', 1)])]
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
