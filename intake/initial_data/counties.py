"""For use by intake/management/commands/load_initial_data.py
    `data` is a required variable
"""

from django.utils.translation import ugettext as _

data = {
    "model": "intake.models.County",
    "instances": [
        {
            "pk": 1,
            "slug": "sanfrancisco",
            "description": _("San Francisco County or City")
        },
        {
            "pk": 2,
            "slug": "contracosta",
            "description": _("Conta Costa County (around Richmond, Walnut Creek, Antioch, or Brentwood)")
        },
        {
            "pk": 3,
            "slug": "other",
            "description": _("Some other county")
        }
    ]
}