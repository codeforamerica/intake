import uuid
from django.db import models
import user_agents
from intake.constants import LANGUAGES_LOOKUP


class Visitor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    first_visit = models.DateTimeField(auto_now_add=True)
    source = models.TextField(null=True)
    referrer = models.TextField(null=True)
    ip_address = models.TextField(null=True)
    user_agent = models.TextField(default='')
    locale = models.TextField(default='')

    def get_uuid(self):
        return self.uuid.hex

    def get_parsed_user_agent(self):
        return user_agents.parse(self.user_agent)

    def get_language_name_in_english(self):
        return LANGUAGES_LOOKUP.get(
            request.LANGUAGE_CODE, request.LANGUAGE_CODE)
