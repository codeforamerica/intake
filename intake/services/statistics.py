"""
This module handles queries to retrieve common statistics
"""
from intake import models, constants
from collections import Counter

TOTAL = 'Total'
ALL = (constants.Organizations.ALL, 'Total (All Organizations)')


def sort_status_type_and_next_step_counts(item_counts):
    """item_counts is a counter"""
    total_count = item_counts.pop(TOTAL, 0)
    sorted_bucket_counts = list(sorted(
        item_counts.items(),
        key=lambda i: i[1],
        reverse=True
    ))
    sorted_bucket_counts.insert(
        0, (TOTAL, total_count))
    return sorted_bucket_counts


def get_status_update_success_metrics():
    """calculates the total number of status updates,
        including the totals by type of status for all orgs and each org.

    Example output (with incorrect numbers):

    [('Total (All Organizations)',
      [('Total', 20),
       ('Submit personal statement', 20),
       ('Eligible', 3),
       ('Not Eligible', 3),
       ('Declined', 2)]),
     ('San Francisco Public Defender',
      [('Total', 2),
       ('Submit personal statement', 2),
       ('Declined', 1),
       ("Can't Proceed", 1)]),
    """
    updates = models.StatusUpdate.objects.all().prefetch_related(
        'application__organization',
        'status_type',
        'next_steps'
    )
    org_status_type_counts = {ALL: Counter()}
    org_status_notification_counts = {ALL: Counter()}
    for update in updates:
        org = (
            update.application.organization.slug,
            update.application.organization.name
        )
        status_type = update.status_type.display_name
        next_steps = [
            next_step.display_name for
            next_step in update.next_steps.all()]
        if not org_status_type_counts.get(org):
            org_status_type_counts[org] = Counter()
        if not org_status_notification_counts.get(org):
            org_status_notification_counts[org] = Counter()
        org_status_type_counts[ALL].update([TOTAL, status_type, *next_steps])
        org_status_type_counts[org].update([TOTAL, status_type, *next_steps])
    data = []
    sorted_orgs = sorted(
        org_status_type_counts.items(),
        key=lambda entry: constants.DEFAULT_ORGANIZATION_ORDER.index(
            entry[0][0])
        )
    for org_tuple, counter in sorted_orgs:
        entry = (org_tuple[1], sort_status_type_and_next_step_counts(counter))
        data.append(entry)
    return data
