from django.contrib import admin
from intake import models


@admin.register(models.FillablePDF)
class FillablePDFAdmin(admin.ModelAdmin):
    pass


@admin.register(models.County)
class CountyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.StatusType)
class StatusTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.NextStep)
class NextStepAdmin(admin.ModelAdmin):
    pass


@admin.register(models.StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    pass


@admin.register(models.StatusNotification)
class StatusNotificationAdmin(admin.ModelAdmin):
    pass
