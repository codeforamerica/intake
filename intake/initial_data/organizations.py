"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from django.utils.translation import ugettext as _

data = {
    "model": "user_accounts.models.Organization",
    "instances": [
        {
            "pk": 2,
            "name": "Code for America", 
            "county_id": 3, # receives 'other' county applications
            "is_receiving_agency": True,
        },
        {
            "pk": 3,
            "name": "San Francisco Public Defender",
            "county_id": 1, # receives SF apps
            "is_receiving_agency": True,
        },
        {
            "pk": 4,
            "name": "Contra Costa Public Defender",
            "county_id": 2, # receives Contra Costa apps
            "is_receiving_agency": True,
        },
        {
            "pk": 1,
            "name": "East Bay Community Law Center",
            "county_id": None,
            "is_receiving_agency": False,
        },
    ]
}