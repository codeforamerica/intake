import datetime
from intake import models
from intake.utils import get_todays_date


def get_submissions_due_for_follow_ups():
    """
    Pulls in submissions that are over a month old
    and which have not sent followups
    """
    today = get_todays_date()
    thirty_days = datetime.timedelta(days=30)
    a_month_ago = today - thirty_days
    qset = models.FormSubmission.objects.filter(
        date_received__lte=a_month_ago,
    ).exclude(
        applicant__events__name=models.ApplicationEvent.FOLLOWUP_SENT
    )
    return qset


def get_followups_count():
    return get_submissions_due_for_follow_ups().count()
