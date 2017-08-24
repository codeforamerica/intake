import factory
from taggit import models


class TagFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'tag-{}'.format(n))

    class Meta:
        model = models.Tag
