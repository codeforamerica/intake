from django.db import models
from django.contrib.postgres.fields import JSONField


class FormSubmission(models.Model):
    date_received = models.DateTimeField(auto_now_add=True)
    answers = JSONField()