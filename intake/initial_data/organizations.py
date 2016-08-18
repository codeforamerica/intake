"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from django.utils.translation import ugettext as _
from intake.constants import Organizations, ORG_NAMES


data = {
    "model": "user_accounts.models.Organization",
    "depends_on": ["intake.models.County"],
    "lookup_keys": ["name"],
    "instances": [
        {
            "name": ORG_NAMES[Organizations.CFA],
            "slug": Organizations.CFA,
            "county_id": None,
            "is_receiving_agency": False,
        },
        {
            "name": ORG_NAMES[Organizations.SF_PUBDEF],
            "slug": Organizations.SF_PUBDEF,
            "county_id": 1, # receives SF apps
            "is_receiving_agency": True,
        },
        {
            "name": ORG_NAMES[Organizations.COCO_PUBDEF],
            "slug": Organizations.COCO_PUBDEF,
            "county_id": 2, # receives Contra Costa apps
            "is_receiving_agency": True,
        },
        {
            "name": ORG_NAMES[Organizations.EBCLC],
            "slug": Organizations.EBCLC,
            "county_id": None,
            "is_receiving_agency": False,
        },
        {
            "name": ORG_NAMES[Organizations.ALAMEDA_PUBDEF],
            "slug": Organizations.ALAMEDA_PUBDEF,
            "county_id": 3,
            "is_receiving_agency": True,
        },
    ]
}