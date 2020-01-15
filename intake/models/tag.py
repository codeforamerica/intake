from django.db import models
from taggit.models import TaggedItemBase


class PurgedSubmissionTagLink(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_submissiontaglink'
        managed = False


class PurgedTag(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"taggit_tag'
        managed = False


class SubmissionTagLink(TaggedItemBase):
    added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        'auth.User',
        models.SET_NULL,
        null=True)
    content_object = models.ForeignKey(
        'intake.FormSubmission',
        models.CASCADE,
        related_name='tag_links',
    )

    class Meta:
        ordering = ['added']
