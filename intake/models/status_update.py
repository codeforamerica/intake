from django.db import models
from intake.constants import PACIFIC_TIME


class StatusUpdate(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status_type = models.ForeignKey(
        'intake.StatusType', on_delete=models.PROTECT)
    next_steps = models.ManyToManyField(
        'intake.NextStep', blank=True)
    additional_information = models.TextField(blank=True)
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    application = models.ForeignKey(
        'intake.Application', on_delete=models.CASCADE,
        related_name='status_updates')
    other_next_step = models.TextField(blank=True)

    def __str__(self):
        return "Sub {} {} on {} by {}".format(
            self.application.form_submission.pk,
            self.status_type.display_name,
            self.updated.astimezone(
                PACIFIC_TIME).strftime("%b %-d %Y"),
            self.author.profile.name)
