import factory
from user_accounts import models


class CountyFactory(factory.DjangoModelFactory):
    slug = factory.Sequence(lambda n: 'county-{}'.format(n))
    name = factory.Sequence(lambda n: 'Fake County {}'.format(n))
    description = factory.Sequence(
        lambda n: (
            'Fake County {} (near Tlön, Uqbar, or Orbis Tertius)'.format(
                n)))

    class Meta:
        model = models.County
