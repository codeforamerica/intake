import datetime
from django.db.models import Q
from intake import models
from intake.utils import get_todays_date
from intake.serializers.form_submission import FollowupInfoSerializer


def get_submissions_due_for_follow_ups(after_id=None):
    """
    Pulls in submissions that are over a month old
    and which have not been sent followups
    """
    today = get_todays_date()
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


def serialized_follow_up_subs(*args, **kwargs):
    submissions = get_submissions_due_for_follow_ups(*args, **kwargs)
    results = FollowupInfoSerializer(submissions, many=True).data
    return len(results), results


def has_usable_contact_preference(serialized_submission):
    """Returns True IFF (sub prefers sms or email
        ) AND (corresponding contact info exists)
    """
    contact_info = serialized_submission.get('contact_information', [])
    for key, contact in contact_info:
        if key in ('sms', 'email'):
            return True
    return False


def get_contactable_followups(*args, **kwargs):
    """Returns followups that prefer email or text messages

    This runs `get_submissions_due_for_follow_ups` and then further
    filters by contact preference criteria.
    Querying on an array within the JSON field is not easy, therefore the
    submissions are filtered after serialization.
    """
    subs = serialized_follow_up_subs(*args, **kwargs)
    return [sub for sub in subs if has_usable_contact_preference(sub)]
