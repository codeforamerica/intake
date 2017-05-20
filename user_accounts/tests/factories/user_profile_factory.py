import factory
from user_accounts import models
from .organization_factory import FakeOrganizationFactory
from .user_factory import UserFactory


class UserProfileFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Fake User {}'.format(n))
    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(FakeOrganizationFactory)

    class Meta:
        model = models.UserProfile
