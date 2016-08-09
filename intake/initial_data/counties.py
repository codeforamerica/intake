"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from intake.constants import Counties, COUNTY_CHOICES

data = {
    "model": "intake.models.County",
    "instances": [
        {
            "pk": 1,
            "slug": Counties.SAN_FRANCISCO, # sanfrancisco
            "description": COUNTY_CHOICES[0][1]
        },
        {
            "pk": 2,
            "slug": Counties.CONTRA_COSTA, # contracosta
            "description": COUNTY_CHOICES[1][1]
        },
        {
            "pk": 3,
            "slug": Counties.OTHER, # other
            "description": COUNTY_CHOICES[2][1]
        }
    ]
}