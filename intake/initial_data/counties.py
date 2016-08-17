"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from intake.constants import Counties, CountyNames, COUNTY_CHOICES

data = {
    "model": "intake.models.County",
    "instances": [
        {
            "pk": 1,
            "slug": Counties.SAN_FRANCISCO, # sanfrancisco
            "name": CountyNames.SAN_FRANCISCO,
            "description": COUNTY_CHOICES[0][1]
        },
        {
            "pk": 2,
            "slug": Counties.CONTRA_COSTA, # contracosta
            "name": CountyNames.CONTRA_COSTA,
            "description": COUNTY_CHOICES[1][1]
        },
        {
            "pk": 3,
            "slug": Counties.ALAMEDA, # contracosta
            "name": CountyNames.ALAMEDA,
            "description": COUNTY_CHOICES[2][1]
        }
    ]
}