from django.db import models
from django.utils import timezone as timezone_utils
from django.contrib.postgres.fields import JSONField
from intake.tasks import log_to_mixpanel

import intake


def remove_pii_from_contact_info(contact_info):
    return list(contact_info.keys())

PII_FILTERS = dict(
    contact_info=remove_pii_from_contact_info)

PII_EXCLUSIONS = (
    'message_content',
)


class ApplicationEvent(models.Model):

    time = models.DateTimeField(default=timezone_utils.now)
    name = models.TextField()
    applicant = models.ForeignKey('intake.Applicant',
                                  on_delete=models.PROTECT, null=False,
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

    def send_filtered_data_to_mixpanel(self):
        filtered_data = {}
        for key, value in self.data.items():
            if key in PII_FILTERS:
                filtered_data[key] = PII_FILTERS[key](value)
            else:
                if key not in PII_EXCLUSIONS:
                    filtered_data[key] = value
        log_to_mixpanel.delay(
            self.applicant_id, self.name, filtered_data)

    @classmethod
    def create(cls, name, applicant_id, **data):
        event = cls(
            name=name,
            applicant_id=applicant_id,
            data=data or {}
        )
        event.save()
        event.send_filtered_data_to_mixpanel()
        return event

    @classmethod
    def log_app_started(
            cls, applicant_id, counties, referrer=None, user_agent=None,
            source=None):
        return cls.create(
            cls.APPLICATION_STARTED, applicant_id,
            counties=counties,
            referrer=referrer,
            user_agent=user_agent,
            source=source)

    @classmethod
    def log_app_errors(cls, applicant_id, errors=None):
        return cls.create(cls.APPLICATION_ERRORS, applicant_id, errors=errors)

    @classmethod
    def log_page_complete(cls, applicant_id, page_name=None):
        return cls.create(
            cls.APPLICATION_PAGE_COMPLETE, applicant_id, page_name=page_name)

    @classmethod
    def log_app_submitted(cls, applicant_id):
        return cls.create(cls.APPLICATION_SUBMITTED, applicant_id)

    @classmethod
    def log_confirmation_sent(
            cls, applicant_id, contact_info, message_content):
        return cls.create(
            cls.CONFIRMATION_SENT, applicant_id, contact_info=contact_info,
            message_content=message_content)

    @classmethod
    def log_followup_sent(cls, applicant_id, contact_info, message_content):
        return cls.create(
            cls.FOLLOWUP_SENT, applicant_id, contact_info=contact_info,
            message_content=message_content)

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

    def __str__(self):
        return 'Applicant(id={})\t{}\t{}\t{}'.format(
            self.applicant_id,
            self.time.strftime('%Y-%m-%d %H:%M:%S'),
            self.name,
            str(self.data))
