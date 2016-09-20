from django.contrib import admin
from . import models


class AddressInline(admin.StackedInline):
    model = models.Address
    extra = 1


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [
        AddressInline
    ]


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass
