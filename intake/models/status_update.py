from django.db import models


class StatusUpdate(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status_type = models.ForeignKey(
        'intake.StatusType', on_delete=models.PROTECT)
    next_steps = models.ManyToManyField(
        'intake.NextStep')
    additional_information = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    application = models.ForeignKey(
        'intake.Application', on_delete=models.CASCADE)
