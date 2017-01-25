import factory
from intake import models


class StatusTypeFactory(factory.DjangoModelFactory):
    label = 'Everything is Awesome'
    display_name = 'Awesome'
    template = 'Dear {{first_name}}, your case is just fantastic!'
    help_text = 'Client has nothing to worry about'
    slug = 'everything-is-awesome'

    class Meta:
        model = models.StatusType
