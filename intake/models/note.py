from django.db import models
from intake.utils import local_time


class PurgedApplicationNote(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_applicationnote'
        managed = False


class ApplicationNote(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', models.PROTECT, related_name='application_notes')
    body = models.TextField()
    submission = models.ForeignKey(
        'intake.FormSubmission', models.CASCADE, related_name='notes')

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
