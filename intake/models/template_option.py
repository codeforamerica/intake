from django.db import models


class TemplateOptionManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class TemplateOption(models.Model):

    label = models.TextField()
    display_name = models.TextField()

    '''
    template should have an arg for custom validators once we determine
    what those should look like
    '''
    template = models.TextField(blank=True)

    help_text = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label
