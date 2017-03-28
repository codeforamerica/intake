from django.db import models


class BaseModel(models.Model):
    """An abstract base model that includes default fields for any table
    """
    # these must be null = True because they will be added to preexisting
    # models
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True
