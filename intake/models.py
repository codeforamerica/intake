from django.db import models
from django.contrib.postgres.fields import JSONField
from pytz import timezone

nice_contact_choices = {
    'voicemail': 'Voicemail',
    'sms': 'Text Message',
    'email': 'Email',
    'snailmail': 'Paper mail'
}

class FormSubmission(models.Model):
    date_received = models.DateTimeField(auto_now_add=True)
    answers = JSONField()

    def get_local_date_received(self, timezone_name='US/Pacific'):
        local_tz = timezone(timezone_name)
        return self.date_received.astimezone(local_tz)

    def get_contact_preferences(self):
        preferences = []
        for k in self.answers:
            if "prefers" in k:
                preferences.append(k[8:])
        return [nice_contact_choices[m] for m in preferences]