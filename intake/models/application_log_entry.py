from django.db import models
from django.utils import timezone as timezone_utils
import intake
from .fields import ContactInfoJSONField


class ApplicationLogEntry(models.Model):
    OPENED = 1
    REFERRED = 2
    PROCESSED = 3
    DELETED = 4
    CONFIRMATION_SENT = 5
    REFERRED_BETWEEN_ORGS = 6

    EVENT_TYPES = (
        (OPENED, "opened"),
        (REFERRED, "referred"),
        (PROCESSED, "processed"),
        (DELETED, "deleted"),
        (CONFIRMATION_SENT, "sent confirmation"),
        (REFERRED_BETWEEN_ORGS, "referred to another org"),
    )

    time = models.DateTimeField(default=timezone_utils.now)
    user = models.ForeignKey('auth.User',
                             models.SET_NULL,
                             null=True,
                             related_name='application_logs')
    organization = models.ForeignKey(
        'user_accounts.Organization',
        models.SET_NULL,
        null=True,
        related_name='logs')
    submission = models.ForeignKey('intake.FormSubmission',
                                   models.SET_NULL,
                                   null=True,
                                   related_name='logs')
    event_type = models.PositiveSmallIntegerField(
        choices=EVENT_TYPES)

    class Meta:
        ordering = ['-time']

    @classmethod
    def log_multiple(cls, event_type, submission_ids,
                     user, time=None, organization=None,
                     organization_id=None):
        if not time:
            time = timezone_utils.now()
        org_kwarg = dict(organization=organization)
        if not organization:
            if organization_id:
                org_kwarg = dict(organization_id=organization_id)
            elif event_type in [cls.PROCESSED, cls.OPENED, cls.DELETED]:
                org_kwarg = dict(organization=user.profile.organization)
        logs = []
        for submission_id in submission_ids:
            log = cls(
                time=time,
                user=user,
                submission_id=submission_id,
                event_type=event_type,
                **org_kwarg
            )
            logs.append(log)
        cls.objects.bulk_create(logs)
        intake.models.ApplicationEvent.from_logs(logs)
        return logs

    @classmethod
    def log_opened(cls, submission_ids, user, time=None):
        intake.models.Application.objects.filter(
            form_submission_id__in=submission_ids,
            organization__profiles__user=user
        ).distinct().update(
            has_been_opened=True)
        return cls.log_multiple(cls.OPENED, submission_ids, user, time)

    @classmethod
    def log_referred_from_one_org_to_another(cls, submission_id,
                                             to_organization_id, user):
        return cls.log_multiple(
            cls.REFERRED_BETWEEN_ORGS, [submission_id], user,
            organization_id=to_organization_id)[0]

    def to_org(self):
        return self.organization

    def from_org(self):
        return self.user.profile.organization


class ApplicantContactedLogEntry(ApplicationLogEntry):
    contact_info = ContactInfoJSONField(default=dict)
    message_sent = models.TextField(blank=True)
