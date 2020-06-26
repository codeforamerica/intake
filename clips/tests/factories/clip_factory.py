import factory
from clips import models


class ClipFactory(factory.DjangoModelFactory):
    title = 'My awesome clip'
    query = 'select id from auth_user;'

    class Meta:
        model = models.Clip
