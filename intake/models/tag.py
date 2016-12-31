from django.db import models
from taggit.models import TaggedItemBase


class ApplicationTag(TaggedItemBase):
    added = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey('auth.User')
    content_object = models.ForeignKey('intake.FormSubmission')

    class Meta:
        ordering = ['added']
