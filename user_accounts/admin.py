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
    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False
