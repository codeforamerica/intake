from django.db import models
from django.utils import timezone as timezone_utils
from django.contrib.postgres.fields import JSONField
import intake


class ApplicationEvent(models.Model):
    time = models.DateTimeField(default=timezone_utils.now)
    name = models.TextField()
    applicant = models.ForeignKey(
        'intake.Applicant',
        models.PROTECT,
        null=False,
        related_name='events')
    data = JSONField()

    APPLICATION_STARTED = 'application_started'
    APPLICATION_SUBMITTED = 'application_submitted'
    APPLICATION_ERRORS = 'application_errors'
    APPLICATION_PAGE_COMPLETE = 'application_page_complete'
    OPENED = "opened"
    REFERRED = "referred"
    PROCESSED = "processed"
    DELETED = "deleted"
    CONFIRMATION_SENT = "sent_confirmation"
    REFERRED_BETWEEN_ORGS = "referred_to_another_org"
    FOLLOWUP_SENT = "sent_followup"

    class Meta:
        ordering = ['-time']

    @classmethod
    def from_logs(cls, logs):
        LogEntry = intake.models.ApplicationLogEntry
        FormSubmission = intake.models.FormSubmission

        applicationLogEntryReference = {
            LogEntry.OPENED: cls.OPENED,
            LogEntry.REFERRED: cls.REFERRED,
            LogEntry.PROCESSED: cls.PROCESSED,
            LogEntry.DELETED: cls.DELETED,
            LogEntry.CONFIRMATION_SENT: cls.CONFIRMATION_SENT,
            LogEntry.REFERRED_BETWEEN_ORGS: cls.REFERRED_BETWEEN_ORGS,
        }

        events = []

        applicant_ids = dict(FormSubmission.objects.filter(
            pk__in=[log.submission_id for log in logs]
        ).values_list('id', 'applicant_id'))
        for log in logs:
            applicant_id = applicant_ids[log.submission_id]
            if applicant_id:
                event = cls(
                    name=applicationLogEntryReference[log.event_type],
                    applicant_id=applicant_id,
                    data={
                        key: value for key, value in vars(log).items()
                        if key in [
                            'submission_id', 'user_id',
                            'organization_id', 'event_type',
                            'id']
                    }
                )
                events.append(event)
        cls.objects.bulk_create(events)
        return events
