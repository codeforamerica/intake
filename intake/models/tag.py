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
        'auth.User', null=True, on_delete=models.SET_NULL)
    content_object = models.ForeignKey(
        'intake.FormSubmission', related_name='tag_links',
        on_delete=models.CASCADE)

    class Meta:
        ordering = ['added']
