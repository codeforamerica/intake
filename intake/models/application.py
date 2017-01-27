from django.db import models


class Application(models.Model):
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.PROTECT,
        related_name='applications')
    form_submission = models.ForeignKey(
        'intake.FormSubmission',
        db_column='formsubmission_id',
        on_delete=models.PROTECT,
        related_name='applications'
    )

    def __str__(self):
        sub = str(self.form_submission.id)
        org = self.organization.name
        return sub+org
