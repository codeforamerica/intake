from django.db import models
from .abstract_base_models import BaseModel


class Application(BaseModel):
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
    was_transferred_out = models.BooleanField(default=False)
    has_been_opened = models.BooleanField(default=False)

    def __str__(self):
        return "Sub {} ({}) to {} on {}".format(
            self.form_submission.id,
            self.form_submission.anonymous_name,
            self.organization.slug,
            self.form_submission.get_local_date_received('%Y-%m-%d'))
