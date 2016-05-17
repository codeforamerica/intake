from django.contrib import admin
from .models import FillablePDF


@admin.register(FillablePDF)
class AuthorAdmin(admin.ModelAdmin):
    pass