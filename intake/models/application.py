from django.db import models


class Application(models.Model):
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.PROTECT)
    form_submission = models.ForeignKey(
        'intake.FormSubmission',
        db_column='formsubmission_id',
        on_delete=models.PROTECT
    )
