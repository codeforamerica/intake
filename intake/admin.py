from django.contrib import admin
from intake import models


@admin.register(models.FillablePDF)
class FillablePDFAdmin(admin.ModelAdmin):
    pass


@admin.register(models.County)
class CountyAdmin(admin.ModelAdmin):
    pass
