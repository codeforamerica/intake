import datetime
from django.db.models import Q
from intake import models, utils
from intake.service_objects import FollowupNotification
import intake.services.events_service as EventsService


def get_submissions_due_for_follow_ups(after_id=None):
    """
    Pulls in submissions that are over 5 weeks old
    and which have not been sent followups
    """
    today = utils.get_todays_date()
    followup_time = datetime.timedelta(days=7*6)
    end_date_criteria = today - followup_time
    date_criteria = Q(date_received__lte=end_date_criteria)
    apps_that_need_followups = models.Application.objects.filter(
        status_updates=None, organization__needs_applicant_followups=True)
    has_at_least_one_app_w_no_update = Q(
        id__in=apps_that_need_followups.values_list(
            'form_submission_id', flat=True))
    if after_id:
        lower_bound = models.FormSubmission.objects.get(
            id=after_id).date_received
        start_date_criteria = Q(date_received__gte=lower_bound)
        date_criteria = date_criteria & start_date_criteria
    exclusion_criteria = ~Q(has_been_sent_followup=True)
    qset = models.FormSubmission.objects.filter(
        has_at_least_one_app_w_no_update & date_criteria & exclusion_criteria
    )
    return qset


def send_followup_notifications(submissions):
    """Sends an email or text via front, based on contact preferences
    """
    notifications = []
    for submission in submissions:
        followup_notification = FollowupNotification(submission)
        followup_notification.send()
        if followup_notification.successes:
            EventsService.followup_sent(
                submission, followup_notification.contact_methods)
            submission.has_been_sent_followup = True
            submission.save()
        notifications.append(followup_notification)
    return notifications


def send_all_followups_that_are_due(*args, **kwargs):
    submissions = get_submissions_due_for_follow_ups(*args, **kwargs)
    send_followup_notifications(submissions)
