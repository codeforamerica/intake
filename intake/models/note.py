from django.db import models
from intake.utils import local_time


class ApplicationNote(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', related_name='application_notes')
    body = models.TextField()
    submission = models.ForeignKey(
        'intake.FormSubmission', related_name='notes')

    class Meta:
        ordering = ['-created']
        permissions = (
            ('view_application_note',
             'Can read the contents of notes from followups'),)

    def __str__(self):
        name = self.user.first_name or self.user.username
        return "{} {} -{}".format(
            local_time(self.created, '%b %-d, %-I:%M %p'),
            self.body,
            name
        )
