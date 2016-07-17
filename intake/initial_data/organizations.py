"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from django.utils.translation import ugettext as _


# Demo:
# {'name': 'Code for America', 'id': 2, 'is_receiving_agency': False, 'blurb': ''}
# {'name': 'SF Public Defender', 'id': 1, 'is_receiving_agency': True, 'blurb': ''}

# Prod:
# {'name': 'Code for America', 'is_receiving_agency': False, 'id': 1, 'blurb': ''}
# {'name': 'SF Public Defender', 'is_receiving_agency': True, 'id': 2, 'blurb': ''}


data = {
    "model": "user_accounts.models.Organization",
    "lookup_keys": ["name"],
    "instances": [
        {
            "name": "Code for America", 
            "county_id": 3, # receives 'other' county applications
            "is_receiving_agency": True,
        },
        {
            "name": "San Francisco Public Defender",
            "county_id": 1, # receives SF apps
            "is_receiving_agency": True,
        },
        {
            "name": "Contra Costa Public Defender",
            "county_id": 2, # receives Contra Costa apps
            "is_receiving_agency": True,
        },
        {
            "name": "East Bay Community Law Center",
            "county_id": None,
            "is_receiving_agency": False,
        },
    ]
}