from django.db import models
from .template_option import TemplateOption, TemplateOptionManager


class StatusType(TemplateOption):
    objects = TemplateOptionManager()
