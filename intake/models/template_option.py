from django.db import models


class TemplateOption(models.Model):

    label = models.TextField()
    display_name = models.TextField()

    '''
    template should have an arg for custom validators once we determine
    what those should look like
    '''
    template = models.TextField()

    help_text = models.TextField()
    slug = models.SlugField()

    class Meta:
        abstract = True
