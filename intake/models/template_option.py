from django.db import models
from intake.validators import template_field_renders_correctly
from intake.utils import render_template_string


class TemplateOptionManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class TemplateOption(models.Model):

    label = models.TextField()
    display_name = models.TextField()
    template = models.TextField(
        blank=True, validators=[template_field_renders_correctly])
    help_text = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    is_a_status_update_choice = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    def render(self, context):
        return render_template_string(self.template, context)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label
