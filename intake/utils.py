import random
from django.utils import timezone
from intake.constants import (
    PACIFIC_TIME, STAFF_NAME_CHOICES, DEFAULT_ORGANIZATION_ORDER
)


def get_todays_date():
    return timezone.now().astimezone(PACIFIC_TIME).date()


def get_random_staff_name():
    return random.choice(STAFF_NAME_CHOICES)


def sort_orgs_in_default_order(orgs):
    if not orgs:
        return orgs
    if hasattr(orgs[0], 'slug'):
        return sorted(
            orgs, key=lambda org: DEFAULT_ORGANIZATION_ORDER.index(org.slug))
    else:
        return sorted(
            orgs,
            key=lambda org: DEFAULT_ORGANIZATION_ORDER.index(org['slug']))


def is_the_weekend():
    """datetime.weekday() returns 0 for Monday, 6 for Sunday
    """
    return timezone.now().weekday() in [5, 6]
