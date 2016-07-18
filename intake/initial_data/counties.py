"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from intake.constants import COUNTY_CHOICES

data = {
    "model": "intake.models.County",
    "instances": [
        {
            "pk": 1,
            "slug": COUNTY_CHOICES[0][0], # sanfrancisco
            "description": COUNTY_CHOICES[0][1]
        },
        {
            "pk": 2,
            "slug": COUNTY_CHOICES[1][0], # contracosta
            "description": COUNTY_CHOICES[1][1]
        },
        {
            "pk": 3,
            "slug": COUNTY_CHOICES[2][0], # other
            "description": COUNTY_CHOICES[2][1]
        }
    ]
}