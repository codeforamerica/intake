from django.conf.urls import url
from phone.views import record, handle_new_message

urlpatterns = [
    # voicemail views
    # these views are public, csrf exempt, and answer to POST data
    url(r'^handle-incoming-call$', record, name='phone-handle_incoming_call'),
    url(r'^handle-new-message$',
        handle_new_message, name='phone-handle_new_message'),
]
