
from django.utils import timezone
from intake.constants import PACIFIC_TIME


def get_todays_date():
    return timezone.now().astimezone(PACIFIC_TIME).date()
