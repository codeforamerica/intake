from django.conf import settings
from django.contrib.auth.models import User
import factory


class UserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'fakeuser{}'.format(n))
    email = factory.Sequence(
        lambda n: 'fakeuser{}@cyber.horse'.format(n))
    password = factory.PostGenerationMethodCall(
        'set_password', settings.TEST_USER_PASSWORD)
    is_active = True

    class Meta:
        model = User
