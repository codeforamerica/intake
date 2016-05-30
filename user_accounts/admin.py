from django.contrib import admin
from . import models

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass