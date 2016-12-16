import datetime
from django.db.models import Q
from intake import models, utils
from intake.service_objects import FollowupNotification


def get_submissions_due_for_follow_ups(after_id=None):
    """
    Pulls in submissions that are over a month old
    and which have not been sent followups
    """
    today = utils.get_todays_date()
    thirty_days = datetime.timedelta(days=30)
    a_month_ago = today - thirty_days
    end_date_criteria = a_month_ago
    date_criteria = Q(date_received__lte=end_date_criteria)
    if after_id:
        lower_bound = models.FormSubmission.objects.get(
            id=after_id).date_received
        start_date_criteria = Q(date_received__gte=lower_bound)
        date_criteria = date_criteria & start_date_criteria
    exclusion_criteria = ~Q(
        applicant__events__name=models.ApplicationEvent.FOLLOWUP_SENT)
    qset = models.FormSubmission.objects.filter(
        date_criteria & exclusion_criteria
    )
    return qset


def send_followup_notifications(submissions):
    """Sends an email or text via front, based on contact preferences
    """
    notifications = []
    for submission in submissions:
        followup_notification = FollowupNotification(submission)
        followup_notification.send()
        notifications.append(followup_notification)
