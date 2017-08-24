from easyaudit.models import CRUDEvent, LoginEvent
from django.contrib import admin


admin.site.unregister(CRUDEvent)
admin.site.unregister(LoginEvent)
